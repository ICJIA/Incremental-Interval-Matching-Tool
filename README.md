Find exact and fuzzy matches of values within a dataframe.
This tool will first screen file names in case there is already an existing file.
It then identifies exact matches. After that it performs its default fuzzy match with caliper range between .0001 and .0005. It displays the match count as it performs the matching. After the first fuzzy match it requests a decision based on the number of matches. If you need more matches it then requests a new caliper to widen the search criteria. Once you have enough matches or all matches have been made it exports the pairs to a csv you determined in the static_var() function.

static_var() variables you need to enter manually (all strings)

    source_file_path = where Python can find the csv you are using (path and name (with extenstion .csv)
    id_col = this is how the pairs are exported in the final product. Each entry should have a unique identifyer and that is what this column is.
    group_col = This is how the program separates the sheet to compare. If you have a column that is 0 and 1 that is what this column is for.
    match_col = This is the value you want to compare the groups against each other on.
    save_to_filename = This is the destination filename AND path