#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(arrow)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
input_path <- if (length(args) >= 1) args[[1]] else "C:/Users/aftik/Downloads/gold_plants.parquet"
output_path <- if (length(args) >= 2) args[[2]] else "public/data/refineries.geojson"
units_path <- if (length(args) >= 3) args[[3]] else "C:/Users/aftik/Downloads/gold_units.parquet"

scalar <- function(x) {
  if (is.null(x) || length(x) == 0) return(NULL)
  if (is.list(x)) {
    if (length(x) == 0 || is.null(x[[1]]) || length(x[[1]]) == 0) return(NULL)
    x <- x[[1]]
  }
  if (length(x) == 0 || is.na(x[[1]])) return(NULL)
  x[[1]]
}

parse_capacities <- function(raw) {
  if (is.null(raw) || length(raw) == 0 || is.na(raw) || !nzchar(raw)) return(list())
  parsed <- tryCatch(fromJSON(raw, simplifyDataFrame = TRUE), error = function(e) NULL)
  if (is.null(parsed) || !is.data.frame(parsed) || !nrow(parsed)) return(list())

  rows <- vector("list", nrow(parsed))
  for (i in seq_len(nrow(parsed))) {
    row <- parsed[i, , drop = FALSE]
    rows[[i]] <- Filter(Negate(is.null), list(
      product_id = if ("productId" %in% names(row)) as.character(scalar(row$productId)) else NULL,
      product_desc = if ("productDesc" %in% names(row)) as.character(scalar(row$productDesc)) else NULL,
      kind = if ("type" %in% names(row)) as.character(scalar(row$type)) else NULL,
      capacity = if ("capacity" %in% names(row)) scalar(row$capacity) else NULL,
      actual_capacity = if ("actualCapacity" %in% names(row)) scalar(row$actualCapacity) else NULL,
      design_capacity = if ("designCapacity" %in% names(row)) scalar(row$designCapacity) else NULL,
      uom = if ("uom" %in% names(row)) as.character(scalar(row$uom)) else NULL
    ))
  }
  rows
}

unit_capacity_rows <- function(raw) {
  rows <- parse_capacities(raw)
  lapply(rows, function(row) {
    out <- row
    if (!is.null(out$kind)) out$kind <- toupper(out$kind)
    if (!is.null(out$actual_capacity) && is.null(out$capacity)) out$capacity <- out$actual_capacity
    out$actual_capacity <- NULL
    out$design_capacity <- NULL
    out
  })
}

clean_value <- function(x) {
  if (length(x) == 0 || is.na(x)) return(NULL)
  if (inherits(x, "POSIXct") || inherits(x, "POSIXt")) return(format(x, "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"))
  if (inherits(x, "Date")) return(format(x, "%Y-%m-%d"))
  x
}

unit_record <- function(units, i) {
  Filter(Negate(is.null), list(
    unit_id = clean_value(units$unit_id[[i]]),
    plant_id = clean_value(units$plant_id[[i]]),
    unit_name = clean_value(units$unit_name[[i]]),
    unit_type_short = clean_value(units$unit_type_short[[i]]),
    unit_type_desc = clean_value(units$unit_type_desc[[i]]),
    unit_type_group = clean_value(units$unit_type_group[[i]]),
    unit_status_desc = clean_value(units$unit_status_desc[[i]]),
    unit_status_group = clean_value(units$unit_status_group[[i]]),
    area_name = clean_value(units$area_name[[i]]),
    power_usage_desc = clean_value(units$power_usage_desc[[i]]),
    renewable = clean_value(units$renewable[[i]]),
    cogen_chp = clean_value(units$cogen_chp[[i]]),
    unit_startup_date = clean_value(units$unit_startup_date[[i]]),
    release_date = clean_value(units$release_date[[i]]),
    capacity = clean_value(units$capacity[[i]]),
    capacity_uom = clean_value(units$capacity_uom[[i]]),
    capacity_kbbl_d = clean_value(units$capacity_kbbl_d[[i]]),
    unit_capacity_feed = clean_value(units$unit_capacity_feed[[i]]),
    unit_capacity_product = clean_value(units$unit_capacity_product[[i]]),
    unit_capacity_feed_kbbl_d = clean_value(units$unit_capacity_feed_kbbl_d[[i]]),
    unit_capacity_product_kbbl_d = clean_value(units$unit_capacity_product_kbbl_d[[i]]),
    unit_capacity_product_desc = clean_value(units$unit_capacity_product_desc[[i]]),
    capacity_product_id = clean_value(units$capacity_product_id[[i]]),
    capacity_rows = unit_capacity_rows(units$unit_capacity[[i]])
  ))
}

unit_sort_key <- function(unit) {
  operational <- identical(unit$unit_status_desc, "Operational")
  commissioned <- identical(unit$unit_status_group, "Commissioned")
  capacity <- suppressWarnings(as.numeric(unit$capacity_kbbl_d))
  if (!length(capacity) || is.na(capacity)) capacity <- -1
  c(if (operational) 0 else 1, if (commissioned) 0 else 1, -capacity)
}

summarize_units <- function(unit_rows) {
  if (!length(unit_rows)) return(list())
  group_labels <- vapply(unit_rows, function(x) {
    clean_value(x$unit_type_short) %||% clean_value(x$unit_type_group) %||% "Unknown"
  }, character(1))
  counts <- sort(table(group_labels), decreasing = TRUE)
  lapply(names(counts), function(name) list(group = name, count = unname(as.integer(counts[[name]]))))
}

`%||%` <- function(a, b) {
  if (is.null(a) || length(a) == 0 || is.na(a) || !nzchar(as.character(a))) b else a
}

plants <- read_parquet(input_path)
units <- if (file.exists(units_path)) read_parquet(units_path) else NULL
units_by_plant <- list()

if (!is.null(units) && nrow(units)) {
  raw_units <- vector("list", nrow(units))
  for (i in seq_len(nrow(units))) {
    raw_units[[i]] <- unit_record(units, i)
  }
  split_units <- split(raw_units, vapply(raw_units, function(x) as.character(x$plant_id %||% ""), character(1)))
  units_by_plant <- lapply(split_units, function(rows) {
    rows <- rows[order(vapply(rows, function(x) unit_sort_key(x)[1], numeric(1)),
                       vapply(rows, function(x) unit_sort_key(x)[2], numeric(1)),
                       vapply(rows, function(x) unit_sort_key(x)[3], numeric(1)))]
    rows
  })
}

features <- list()

for (i in seq_len(nrow(plants))) {
  lat <- plants$latitude[[i]]
  lon <- plants$longitude[[i]]
  if (is.na(lat) || is.na(lon)) next

  props <- Filter(Negate(is.null), list(
    plant_id = clean_value(plants$plant_id[[i]]),
    plant_name = clean_value(plants$plant_name[[i]]),
    owner_name = clean_value(plants$owner_name[[i]]),
    operator_name = clean_value(plants$operator_name[[i]]),
    parent_company = clean_value(plants$parent_company[[i]]),
    plant_status_desc = clean_value(plants$plant_status_desc[[i]]),
    city = clean_value(plants$city[[i]]),
    state_name = clean_value(plants$state_name[[i]]),
    country_name = clean_value(plants$country_name[[i]]),
    market_region_name = clean_value(plants$market_region_name[[i]]),
    trading_region_name = clean_value(plants$trading_region_name[[i]]),
    country_padd = clean_value(plants$country_padd[[i]]),
    subcontinent = clean_value(plants$subcontinent[[i]]),
    primary_sic_desc = clean_value(plants$primary_sic_desc[[i]]),
    plant_sectors = clean_value(plants$plant_sectors[[i]]),
    primary_fuel = clean_value(plants$primary_fuel[[i]]),
    secondary_fuel = clean_value(plants$secondary_fuel[[i]]),
    no_employees = clean_value(plants$no_employees[[i]]),
    startup_date = clean_value(plants$startup_date[[i]]),
    release_date = clean_value(plants$release_date[[i]]),
    crud_capacity_bbl_d = clean_value(plants$crud_capacity_bbl_d[[i]]),
    crud_capacity_kbbl_d = clean_value(plants$crud_capacity_kbbl_d[[i]]),
    capacity_count = clean_value(plants$capacity_count[[i]]),
    sectors_count = clean_value(plants$sectors_count[[i]]),
    plant_capacities = parse_capacities(plants$capacity[[i]])
  ))

  plant_units <- units_by_plant[[as.character(plants$plant_id[[i]])]]
  if (!is.null(plant_units) && length(plant_units)) {
    props$refinery_units <- plant_units
    props$refinery_unit_count <- length(plant_units)
    props$refinery_unit_summary <- summarize_units(plant_units)
  }

  features[[length(features) + 1]] <- list(
    type = "Feature",
    geometry = list(type = "Point", coordinates = list(lon, lat)),
    properties = props
  )
}

geojson <- list(
  type = "FeatureCollection",
  name = "gold_plants_refineries",
  generated_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  source = list(
    plants = "IIR gold plants analytical extract",
    units = "IIR gold units analytical extract"
  ),
  coverage_note = paste(
    "Rich plant and unit detail; not a canonical EIA U.S. refinery roster.",
    "Use EIA Refinery Capacity Report counts/status/capacity for national completeness checks."
  ),
  features = features
)

dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)
write_json(geojson, output_path, auto_unbox = TRUE, null = "null", pretty = FALSE)
cat(sprintf("Wrote %s features to %s\n", length(features), output_path))
