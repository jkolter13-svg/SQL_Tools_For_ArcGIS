"""
============================================================
GEODATABASE TABLE INVENTORY SCRIPT
============================================================

What this does:
    Connects to an ArcGIS geodatabase (via an .sde connection file or
    local workspace), walks through every standalone table it finds,
    and records a full inventory of:
        - Table name
        - Row count
        - Every field in that table (name, data type, and length)
    
    This script only inventories standalone tables (ListTables), not feature classes, 
    so any spatial asset layers in the geodatabase won't show up unless you add 
    a parallel loop using arcpy.ListFeatureClasses()

    The result is written out to a single CSV file in "long" format
    (one row per field, not per table), which makes it easy to filter,
    sort, or search by table or field name later in Excel.

Why this exists:
    Useful as a starting point before any schema migration, audit, or
    cleanup - gives you a snapshot of exactly what fields and tables
    currently exist before anything changes. If a table can't be read
    (locked, permissions issue, corrupt schema, etc.), the script logs
    the error directly into the CSV and keeps going rather than
    stopping the whole run.

Before running:
    1. Update arcpy.env.workspace below to point at your geodatabase
       connection (.sde file) or workspace path.
    2. Update output_csv to wherever you want the resulting CSV saved.
    3. Run from an environment that has ArcPy available (e.g. the
       Python environment bundled with ArcGIS Pro).

Note:
    This only inventories standalone TABLES (arcpy.ListTables()), not
    spatial feature classes/layers. If you also need spatial asset
    layers included, add a parallel loop using
    arcpy.ListFeatureClasses().

Credits:
    Jonathan Kolterman 2026
    email jkolterman13@gmail.com
    linkedin https://www.linkedin.com/in/jonathan-kolterman-1808342b8
============================================================
"""
# =========================================================================================================================
import arcpy      # ArcGIS Python API - gives us access to geodatabase tools (ListTables, GetCount, ListFields, etc.)
import csv         # Standard library module for writing CSV (comma-separated values) files
# =========================================================================================================================
# --- EDIT THIS PATH ---
# Set the ArcPy "workspace" - this tells ArcPy which geodatabase/connection to look inside.
# Here it's pointed at a .sde file, which is a connection file to an enterprise (SQL Server/Oracle/etc.) geodatabase.
arcpy.env.workspace = r"C:\path\to\your\connection.sde"

# Full path (including filename) where the resulting inventory CSV will be saved.
output_csv = r"C:\path\to\output\table_inventory.csv"
# =========================================================================================================================

# Ask ArcPy for a list of every standalone table in the current workspace.
# Note: this returns TABLES only (not feature classes/spatial layers) - use arcpy.ListFeatureClasses()
# separately if you also need spatial layers included in the inventory.
tables = arcpy.ListTables()
# =========================================================================================================================

# Open (or create) the output CSV file for writing.
# mode="w" = write mode (overwrites if file already exists)
# newline="" = prevents Python from adding extra blank lines between rows on Windows
# encoding="utf-8" = ensures special characters in field/table names don't break the file
with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
    
    # Create a CSV writer object bound to our open file - this lets us write rows with .writerow()
    writer = csv.writer(csvfile)
    
    # Write the header row first, so the CSV has column labels when opened in Excel/etc.
    writer.writerow(["Table", "RowCount", "FieldName", "FieldType", "FieldLength"])

    # Loop through every table name we found above, one at a time
    for tbl in tables:
        
        # Print progress to the console so you can watch it work / see where it is if it hangs
        print(f"Processing {tbl}...")

        # Wrap each table's processing in a try/except so that ONE bad/locked/corrupt table
        # doesn't crash the entire script and lose all the progress made on previous tables.
        try:
            # GetCount returns a "Result" object, not a plain number - [0] pulls the actual
            # count value out of it (as a string). This gives us the total row count for the table.
            count = arcpy.management.GetCount(tbl)[0]
            
            # ListFields returns a list of Field objects for this table, each describing
            # one column (name, data type, length, etc.)
            fields = arcpy.ListFields(tbl)

            # Write ONE row per field in the table (so a table with 10 fields produces 10 CSV rows,
            # each repeating the table name and row count, but with different field info).
            # This is a denormalized/"long" format - convenient for filtering/sorting in Excel later.
            for f in fields:
                writer.writerow([tbl, count, f.name, f.type, f.length])

        # If anything above fails (e.g., table is locked, permissions issue, schema is corrupt),
        # catch the error here instead of letting the whole script crash.
        except Exception as e:
            # Print the error to console so you see it happen in real time
            print(f"  SKIPPED {tbl}: {e}")
            
            # Also log the failure directly into the CSV itself, so the output file has a permanent
            # record of which tables failed and why - useful for following up later.
            writer.writerow([tbl, f"ERROR: {e}", "", "", ""])
            
            # Skip the rest of this loop iteration and move on to the next table
            continue
# =========================================================================================================================
# This runs after the loop finishes and the file has been closed (the "with" block auto-closes it).
# Lets you know the script is done and where to find the results.
print(f"\nDone. CSV written to: {output_csv}")