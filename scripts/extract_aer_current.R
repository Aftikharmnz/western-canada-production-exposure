# Narrow XLS reader: Python owns normalization, identity, location and exports.
suppressPackageStartupMessages(library(readxl))
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("usage: extract_aer_current.R <st53|st39> <input.xls> <output.csv>")
kind <- args[[1]]
x <- suppressMessages(read_excel(args[[2]], sheet = if (kind == "st53") "BITUMEN" else "VAR0800-ST39Extracts_xls", col_names = FALSE, col_types = "text"))
out <- list()
emit <- function(operator, facility, approval, stream, period, value, units, area = "", recovery = "") {
  out[[length(out) + 1L]] <<- data.frame(operator, facility, approval, stream, period,
    value, units, area, recovery, stringsAsFactors = FALSE)
}
if (kind == "st53") {
  title <- x[[1]][1]
  year <- regmatches(title, regexpr("20[0-9]{2}", title))
  if (!grepl("Per Calendar Day", x[[6]][3], fixed = TRUE) || !grepl("m\u00b3", x[[6]][3], fixed = TRUE)) stop("Unrecognized ST53 rate units")
  if (!identical(as.character(unlist(x[4, 6:17], use.names = FALSE)), month.abb)) stop("Unrecognized ST53 month columns")
  if (length(year) != 1 || !grepl("^[0-9]{4}$", year)) stop("Missing ST53 issue year")
  for (i in seq.int(5, nrow(x))) {
    approval <- x[[4]][i]
    if (is.na(approval) || !grepl("^[0-9]+[A-Za-z]*$", approval)) next
    for (month in 1:12) {
      value <- suppressWarnings(as.numeric(x[[month + 5]][i]))
      if (!is.finite(value) || value < 0) next
      emit(x[[1]][i], x[[2]][i], approval, "In-situ bitumen", sprintf("%s-%02d", year, month), value, "m3/d", x[[3]][i], x[[5]][i])
    }
  }
} else if (kind == "st39") {
  title <- unlist(x[1:5,], use.names = FALSE)
  issue <- title[!is.na(title) & grepl("Production Month/Year:", title, fixed = TRUE)][1]
  year <- regmatches(issue, regexpr("20[0-9]{2}", issue))
  issue_month <- match(sub(".*Production Month/Year:\\s*([A-Za-z]+).*", "\\1", issue), month.name)
  if (!is.finite(issue_month) || length(year) != 1) stop("Missing ST39 issue date")
  blocks <- which(!is.na(x[[1]]) & grepl(" - ABOS", x[[1]], fixed = TRUE))
  section_rows <- which(!is.na(x[[1]]) & (startsWith(x[[1]], "Crude Bitumen (") | startsWith(x[[1]], "Synthetic Crude Oil (")))
  for (i in section_rows) {
    if (!grepl("m\u00b3", x[[1]][i], fixed = TRUE)) stop("Unrecognized ST39 volume units")
    block <- max(blocks[blocks < i])
    block_name <- x[[1]][block]
    approval <- sub(".* - (ABOS[0-9]+) .*", "\\1", block_name)
    operator <- sub(" - ABOS[0-9]+.*", "", block_name)
    facility <- sub(".*ABOS[0-9]+\\s+", "", block_name)
    labels <- x[[1]][i:min(i + 12, nrow(x))]
    offset <- which(!is.na(labels) & labels == "Production")[1]
    if (is.na(offset)) next
    for (col in 2:ncol(x)) {
      month <- match(x[[col]][i + 1], month.name)
      if (is.na(month) || month > issue_month) next
      value <- suppressWarnings(as.numeric(x[[col]][i + offset - 1]))
      if (!is.finite(value) || value < 0) next
      emit(operator, facility, approval, if (startsWith(x[[1]][i], "Crude Bitumen")) "Mined bitumen gross" else "Synthetic crude oil", sprintf("%s-%02d", year, month), value, "m3/month")
    }
  }
} else stop("Unknown source")
if (!length(out)) stop("No valid production records extracted")
dir.create(dirname(args[[3]]), recursive = TRUE, showWarnings = FALSE)
write.csv(do.call(rbind, out), args[[3]], row.names = FALSE, na = "")
