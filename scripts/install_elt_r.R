# Use the same report reader as the verified historical extraction.
if (is.null(getOption("repos")) || identical(unname(getOption("repos")), "@CRAN@")) {
  options(repos = c(CRAN = "https://cloud.r-project.org"))
}
required <- c("cellranger", "tibble", "cpp11", "progress")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) install.packages(missing)
if (!requireNamespace("readxl", quietly = TRUE) || as.character(packageVersion("readxl")) != "1.4.5") {
  install.packages("https://cran.r-project.org/src/contrib/Archive/readxl/readxl_1.4.5.tar.gz", repos = NULL, type = "source")
}
stopifnot(as.character(packageVersion("readxl")) == "1.4.5")
sessionInfo()
