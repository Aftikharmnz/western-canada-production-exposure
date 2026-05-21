suppressPackageStartupMessages(library(readxl))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop("usage: Rscript extract_aer_st39_synthetic.R <st39_xls> <output_csv>", call. = FALSE)
}

input_path <- args[[1]]
output_path <- args[[2]]

month_lookup <- c(
  January = "01", February = "02", March = "03", April = "04",
  May = "05", June = "06", July = "07", August = "08",
  September = "09", October = "10", November = "11", December = "12"
)

x <- read_excel(
  input_path,
  sheet = "VAR0800-ST39Extracts_xls",
  col_names = FALSE,
  col_types = "text"
)

block_starts <- which(grepl(" - ABOS", x[[1]], fixed = TRUE))
synth_rows <- which(grepl("Synthetic Crude Oil", x[[1]], ignore.case = TRUE))

title_values <- unlist(x[1:min(nrow(x), 5), ], use.names = FALSE)
period_text <- title_values[grepl("Production Month/Year:", title_values, fixed = TRUE)][1]
if (is.na(period_text)) {
  stop("Could not find ST39 production month/year header.", call. = FALSE)
}
period_month <- sub(".*Production Month/Year:\\s*([A-Za-z]+)\\s+([0-9]{4}).*", "\\1", period_text)
period_year <- sub(".*Production Month/Year:\\s*([A-Za-z]+)\\s+([0-9]{4}).*", "\\2", period_text)

rows <- list()
for (header_row in synth_rows) {
  block_start <- suppressWarnings(max(block_starts[block_starts < header_row]))
  if (!is.finite(block_start)) next

  block_name <- x[[1]][block_start]
  approval <- sub(".* - (ABOS[0-9]+) .*", "\\1", block_name)
  operator <- sub(" - ABOS[0-9]+.*", "", block_name)
  facility <- sub(".*ABOS[0-9]+\\s+", "", block_name)

  search_to <- min(nrow(x), header_row + 12)
  labels <- x[[1]][header_row:search_to]
  prod_offset <- which(labels == "Production")[1]
  if (is.na(prod_offset)) next

  month_header <- unlist(x[header_row + 1, ], use.names = FALSE)
  prod_values <- unlist(x[header_row + prod_offset - 1, ], use.names = FALSE)

  for (col in seq_along(month_header)) {
    month_name <- month_header[[col]]
    if (is.na(month_name) || !(month_name %in% names(month_lookup))) next
    # ST39 current issues normally carry the named current production month and
    # zero-filled future months. Keep any positive month, but derive year from
    # the issue header.
    volume <- suppressWarnings(as.numeric(prod_values[[col]]))
    if (!is.finite(volume) || volume <= 0) next
    rows[[length(rows) + 1]] <- data.frame(
      operator = operator,
      approval = approval,
      facility = facility,
      period = paste0(period_year, "-", month_lookup[[month_name]]),
      header_period = paste(period_month, period_year),
      volume_m3 = volume,
      stringsAsFactors = FALSE
    )
  }
}

out <- if (length(rows)) do.call(rbind, rows) else data.frame(
  operator = character(),
  approval = character(),
  facility = character(),
  period = character(),
  header_period = character(),
  volume_m3 = numeric(),
  stringsAsFactors = FALSE
)

dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)
write.csv(out, output_path, row.names = FALSE, na = "")
