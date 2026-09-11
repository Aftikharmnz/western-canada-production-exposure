# Narrow XLS reader: Python owns normalization, identity, location and exports.
suppressPackageStartupMessages(library(readxl))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("usage: extract_aer_current.R <st53|st39> <input.xls> <output.csv>")
kind <- args[[1]]
if (!(kind %in% c("st53", "st39"))) stop("Unknown source")
sheet <- if (kind == "st53") "BITUMEN" else "VAR0800-ST39Extracts_xls"
if (!(sheet %in% excel_sheets(args[[2]]))) stop("Unrecognized AER workbook sheet schema")
x <- suppressMessages(read_excel(args[[2]], sheet = sheet, col_names = FALSE, col_types = "text"))
if (nrow(x) < 6 || ncol(x) < 14) stop("Truncated AER publication")
out <- list()
production_value <- function(cell) {
  if (is.na(cell) || !nzchar(trimws(cell))) return(NA_real_)
  value <- suppressWarnings(as.numeric(cell))
  if (!is.finite(value) || value < 0) stop(paste("Invalid production observation:", cell))
  value
}
emit <- function(operator, facility, approval, stream, period, value, units, area = "", recovery = "") {
  out[[length(out) + 1L]] <<- data.frame(operator, facility, approval, stream, period,
    value, units, area, recovery, stringsAsFactors = FALSE)
}
if (kind == "st53") {
  title <- x[[1]][1]
  if (is.na(title) || !grepl("ST-53", title, fixed = TRUE)) stop("Unrecognized ST53 report title")
  year <- regmatches(title, regexpr("20[0-9]{2}", title))
  issue <- trimws(x[[1]][2])
  issue_month <- match(sub("^([A-Za-z]+).*", "\\1", issue), month.name)
  issue_year <- regmatches(issue, regexpr("20[0-9]{2}", issue))
  if (!grepl("Per Calendar Day", x[[6]][3], fixed = TRUE) || !grepl("m\u00b3", x[[6]][3], fixed = TRUE)) stop("Unrecognized ST53 rate units")
  if (!identical(as.character(unlist(x[4, 6:17], use.names = FALSE)), month.abb)) stop("Unrecognized ST53 month columns")
  if (length(year) != 1 || !grepl("^[0-9]{4}$", year)) stop("Missing ST53 issue year")
  if (!is.finite(issue_month) || !identical(year, issue_year)) stop("Missing or inconsistent ST53 issue month")
  if (!identical(as.character(unlist(x[4, 1:5], use.names = FALSE)), c("Operator", "Scheme Name", "Area", "Approval Number", "Recovery Method"))) stop("Unrecognized ST53 identity columns")
  for (i in seq.int(5, nrow(x))) {
    approval <- x[[4]][i]
    if (is.na(approval) || !nzchar(trimws(approval))) next
    if (!grepl("^[0-9]+[A-Za-z]*$", approval)) stop("Unrecognized ST53 approval identifier")
    for (month in seq_len(issue_month)) {
      value <- production_value(x[[month + 5]][i])
      if (is.na(value)) next
      emit(x[[1]][i], x[[2]][i], approval, "In-situ bitumen", sprintf("%s-%02d", year, month), value, "m3/d", x[[3]][i], x[[5]][i])
    }
  }
} else if (kind == "st39") {
  title <- unlist(x[1:5,], use.names = FALSE)
  issue <- title[!is.na(title) & grepl("Production Month/Year:", title, fixed = TRUE)][1]
  year <- regmatches(issue, regexpr("20[0-9]{2}", issue))
  issue_month <- match(sub(".*Production Month/Year:\\s*([A-Za-z]+).*", "\\1", issue), month.name)
  if (!is.finite(issue_month) || length(year) != 1 || !grepl("^20[0-9]{2}$", year)) stop("Missing ST39 issue date")
  blocks <- which(!is.na(x[[1]]) & grepl(" - ABOS", x[[1]], fixed = TRUE))
  section_rows <- which(!is.na(x[[1]]) & (startsWith(x[[1]], "Crude Bitumen (") | startsWith(x[[1]], "Synthetic Crude Oil (")))
  for (i in section_rows) {
    if (!grepl("m\u00b3", x[[1]][i], fixed = TRUE)) stop("Unrecognized ST39 volume units")
    preceding <- blocks[blocks < i]
    if (!length(preceding)) stop("ST39 production section has no facility identity")
    block <- max(preceding)
    block_name <- x[[1]][block]
    approval <- sub(".* - (ABOS[0-9]+) .*", "\\1", block_name)
    if (!grepl("^ABOS[0-9]+$", approval)) stop("Unrecognized ST39 approval identifier")
    operator <- sub(" - ABOS[0-9]+.*", "", block_name)
    facility <- sub(".*ABOS[0-9]+\\s+", "", block_name)
    labels <- x[[1]][i:min(i + 12, nrow(x))]
    offset <- which(!is.na(labels) & labels == "Production")
    if (length(offset) != 1) stop("ST39 product section has missing/ambiguous Production row")
    if (!identical(as.character(unlist(x[i + 1, 2:13], use.names = FALSE)), month.name)) stop("Unrecognized ST39 month columns")
    if (!identical(x[[14]][i + 1], year)) stop("Inconsistent ST39 section year")
    for (col in 2:ncol(x)) {
      month <- match(x[[col]][i + 1], month.name)
      if (is.na(month) || month > issue_month) next
      value <- production_value(x[[col]][i + offset - 1])
      if (is.na(value)) next
      emit(operator, facility, approval, if (startsWith(x[[1]][i], "Crude Bitumen")) "Mined bitumen gross" else "Synthetic crude oil", sprintf("%s-%02d", year, month), value, "m3/month")
    }
  }
} else stop("Unknown source")
if (!length(out)) stop("No valid production records extracted")
archive_year <- sub("^aer_st(?:53|39)_(20[0-9]{2})\\.xlsx?$", "\\1", basename(args[[2]]), perl = TRUE)
if (grepl("^20[0-9]{2}$", archive_year) && !identical(archive_year, year)) stop("AER publication year does not match archive identity")
dir.create(dirname(args[[3]]), recursive = TRUE, showWarnings = FALSE)
write.csv(do.call(rbind, out), args[[3]], row.names = FALSE, na = "")
