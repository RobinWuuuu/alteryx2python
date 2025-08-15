comprehensive_guide = {
    "Dbfileinput": (
        r"""
            SQL Input Tool: Convert Alteryx file input to SQL table references or data loading operations.
            
            Key SQL Considerations:
            1. For database connections: Use direct table references (e.g., FROM database.schema.table)
            2. For flat files: Use appropriate SQL file loading functions based on database type
            3. Handle file paths and connection strings appropriately
            4. Consider data type mappings between file formats and SQL types
            
            SQL Implementation:
            - Use direct table references: SELECT * FROM database.schema.table_name
            - For CSV files: Use database-specific file loading (e.g., COPY, BULK INSERT, LOAD DATA)
            - Handle column names and data types appropriately
            - Include proper error handling for file access issues
        """
        ),

    "Alteryxselect": (
        r"""
            SQL SELECT Tool: Convert Alteryx field selection to SQL column selection and data type handling.
            
            Key SQL Operations:
            1. Column selection: Use explicit column names in SELECT clause
            2. Data type conversion: Use CAST() or CONVERT() functions
            3. Column renaming: Use AS keyword for aliases
            4. Handle deselected fields by excluding them from SELECT
            
            SQL Implementation:
            - SELECT specific columns: SELECT col1, col2, col3 FROM table
            - Data type conversion: CAST(column AS data_type) or CONVERT(data_type, column)
            - Column aliases: SELECT col1 AS new_name FROM table
            - Exclude unwanted columns by not including them in SELECT
        """
        ),

    "Filter": (
        r"""
            SQL WHERE Tool: Convert Alteryx filter conditions to SQL WHERE clauses.
            
            Key SQL Operations:
            1. Single conditions: Use WHERE column = value
            2. Multiple conditions: Use AND/OR operators
            3. String comparisons: Use LIKE, IN, or exact matching
            4. Numeric comparisons: Use >, <, >=, <=, =, !=
            5. NULL handling: Use IS NULL or IS NOT NULL
            
            SQL Implementation:
            - Basic filter: WHERE column > 1000
            - Multiple conditions: WHERE col1 > 100 AND col2 IN ('A', 'B')
            - String patterns: WHERE column LIKE '%pattern%'
            - NULL checks: WHERE column IS NOT NULL
        """
        ),

    "Join": (
        r"""
            SQL JOIN Tool: Convert Alteryx join operations to SQL JOIN clauses.
            
            Key SQL Operations:
            1. Join types: INNER, LEFT, RIGHT, FULL OUTER JOIN
            2. Join conditions: ON clause with column matching
            3. Multiple joins: Chain JOIN clauses
            4. Column handling: Use table aliases to avoid ambiguity
            
            SQL Implementation:
            - INNER JOIN: FROM table1 INNER JOIN table2 ON table1.id = table2.id
            - LEFT JOIN: FROM table1 LEFT JOIN table2 ON table1.id = table2.id
            - Multiple joins: FROM t1 JOIN t2 ON t1.id = t2.id JOIN t3 ON t2.id = t3.id
            - Use aliases: FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id
        """
        ),

    "Union": (
        r"""
            SQL UNION Tool: Convert Alteryx union operations to SQL UNION clauses.
            
            Key SQL Operations:
            1. UNION: Combines results and removes duplicates
            2. UNION ALL: Combines results and keeps duplicates
            3. Column alignment: Ensure same number and compatible data types
            4. Order handling: Use ORDER BY at the end
            
            SQL Implementation:
            - UNION: SELECT col1, col2 FROM table1 UNION SELECT col1, col2 FROM table2
            - UNION ALL: SELECT col1, col2 FROM table1 UNION ALL SELECT col1, col2 FROM table2
            - With ORDER BY: (SELECT col1 FROM table1) UNION (SELECT col1 FROM table2) ORDER BY col1
         """
    ),

    "Summarize": (
        r"""
            SQL GROUP BY Tool: Convert Alteryx summarize operations to SQL GROUP BY with aggregations.
            
            Key SQL Operations:
            1. GROUP BY: Group by specified columns
            2. Aggregation functions: COUNT, SUM, AVG, MIN, MAX, etc.
            3. HAVING: Filter aggregated results
            4. Multiple aggregations: Combine different functions
            
            SQL Implementation:
            - Basic aggregation: SELECT col1, SUM(col2) FROM table GROUP BY col1
            - Multiple aggregations: SELECT col1, COUNT(*), SUM(col2), AVG(col3) FROM table GROUP BY col1
            - With HAVING: SELECT col1, SUM(col2) FROM table GROUP BY col1 HAVING SUM(col2) > 1000
        """
        ),

    "Formula": (
        r"""
            SQL Expression Tool: Convert Alteryx formulas to SQL expressions and calculated columns.
            
            Key SQL Operations:
            1. Calculated columns: Use expressions in SELECT clause
            2. CASE statements: Handle conditional logic
            3. String functions: CONCAT, SUBSTRING, UPPER, LOWER, etc.
            4. Date functions: DATE functions, date arithmetic
            5. Mathematical operations: Standard arithmetic operators
            
            SQL Implementation:
            - Simple calculation: SELECT col1, col2, col1 + col2 AS total FROM table
            - CASE statement: SELECT col1, CASE WHEN col1 > 100 THEN 'High' ELSE 'Low' END AS category
            - String operations: SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM table
            - Date operations: SELECT DATE_ADD(date_col, INTERVAL 1 DAY) AS next_day FROM table
        """
    ),

    "Sort": (
        r"""
            SQL ORDER BY Tool: Convert Alteryx sort operations to SQL ORDER BY clauses.
            
            Key SQL Operations:
            1. Single column sort: ORDER BY column_name
            2. Multiple column sort: ORDER BY col1, col2, col3
            3. Sort direction: ASC (default) or DESC
            4. Mixed directions: ORDER BY col1 ASC, col2 DESC
            
            SQL Implementation:
            - Single sort: SELECT * FROM table ORDER BY column_name
            - Multiple columns: SELECT * FROM table ORDER BY col1, col2 DESC
            - Mixed directions: SELECT * FROM table ORDER BY col1 ASC, col2 DESC, col3 ASC
        """
    ),

    "Unique": (
        r"""
            SQL DISTINCT Tool: Convert Alteryx unique operations to SQL DISTINCT or GROUP BY.
            
            Key SQL Operations:
            1. DISTINCT: Remove duplicate rows based on all columns
            2. GROUP BY: Remove duplicates based on specific columns
            3. COUNT DISTINCT: Count unique values
            4. Multiple column uniqueness: Use GROUP BY with multiple columns
            
            SQL Implementation:
            - Remove all duplicates: SELECT DISTINCT * FROM table
            - Remove duplicates by specific columns: SELECT col1, col2 FROM table GROUP BY col1, col2
            - Count unique values: SELECT COUNT(DISTINCT column_name) FROM table
        """
    ),

    "Sample": (
        r"""
            SQL Sampling Tool: Convert Alteryx sample operations to SQL sampling functions.
            
            Key SQL Operations:
            1. Random sampling: Use RAND() or database-specific functions
            2. Percentage sampling: Use LIMIT with calculations
            3. Systematic sampling: Use ROW_NUMBER() with modulo
            4. Stratified sampling: Use PARTITION BY with ROW_NUMBER()
            
            SQL Implementation:
            - Random sample: SELECT * FROM table ORDER BY RAND() LIMIT 100
            - Percentage sample: SELECT * FROM table WHERE RAND() < 0.1
            - Systematic sample: SELECT * FROM (SELECT *, ROW_NUMBER() OVER() as rn FROM table) t WHERE rn % 10 = 0
        """
    ),

    "TextInput": (
        r"""
            SQL Data Creation Tool: Convert Alteryx text input to SQL data creation or constants.
            
            Key SQL Operations:
            1. Constant values: Use literal values in SELECT
            2. Data creation: Use VALUES clause or UNION ALL
            3. Parameter substitution: Use variables or parameters
            4. Lookup tables: Create reference data inline
            
            SQL Implementation:
            - Constants: SELECT 'constant_value' AS column_name
            - Multiple rows: SELECT 'value1' AS col UNION ALL SELECT 'value2' AS col
            - With parameters: SELECT @parameter_value AS column_name
        """
    ),

    "Output": (
        r"""
            SQL Output Tool: Convert Alteryx output operations to SQL result handling.
            
            Key SQL Operations:
            1. Final SELECT: Use as the main query result
            2. INTO clause: Insert results into another table
            3. CREATE TABLE AS: Create new table from results
            4. Temporary tables: Use CTEs or temp tables for intermediate results
            
            SQL Implementation:
            - Final result: SELECT * FROM final_cte
            - Insert into table: INSERT INTO target_table SELECT * FROM source_query
            - Create table: CREATE TABLE new_table AS SELECT * FROM source_query
            - CTE result: WITH final_result AS (SELECT * FROM processed_data) SELECT * FROM final_result
        """
    ),

    "DataCleaning": (
        r"""
            SQL Data Cleaning Tool: Convert Alteryx data cleaning operations to SQL data quality functions.
            
            Key SQL Operations:
            1. NULL handling: COALESCE, ISNULL, or CASE statements
            2. String cleaning: TRIM, REPLACE, REGEXP_REPLACE
            3. Data validation: CASE statements with conditions
            4. Type conversion: CAST, CONVERT functions
            5. Duplicate removal: DISTINCT or GROUP BY
            
            SQL Implementation:
            - Handle NULLs: COALESCE(column_name, 'default_value')
            - String cleaning: TRIM(REPLACE(column_name, 'old', 'new'))
            - Data validation: CASE WHEN column_name IS NOT NULL AND column_name != '' THEN column_name ELSE 'default' END
            - Type conversion: CAST(column_name AS INTEGER)
        """
    ),

    "Aggregate": (
        r"""
            SQL Aggregation Tool: Convert Alteryx aggregate operations to SQL aggregation functions.
            
            Key SQL Operations:
            1. Window functions: ROW_NUMBER(), RANK(), DENSE_RANK()
            2. Running totals: SUM() OVER (ORDER BY column)
            3. Group aggregations: Standard GROUP BY functions
            4. Conditional aggregations: SUM(CASE WHEN condition THEN value ELSE 0 END)
            
            SQL Implementation:
            - Window functions: SELECT *, ROW_NUMBER() OVER (ORDER BY column_name) as rn FROM table
            - Running totals: SELECT *, SUM(value) OVER (ORDER BY date) as running_total FROM table
            - Conditional aggregation: SELECT category, SUM(CASE WHEN status = 'active' THEN amount ELSE 0 END) as active_total FROM table GROUP BY category
        """
    ),

    "Transform": (
        r"""
            SQL Transformation Tool: Convert Alteryx transform operations to SQL data transformation functions.
            
            Key SQL Operations:
            1. Pivot operations: Use conditional aggregation with CASE statements
            2. Unpivot operations: Use UNION ALL or CROSS JOIN with VALUES
            3. Data reshaping: Use window functions and conditional logic
            4. Complex transformations: Combine multiple SQL functions
            
            SQL Implementation:
            - Pivot: SELECT id, SUM(CASE WHEN category = 'A' THEN value ELSE 0 END) as cat_a, SUM(CASE WHEN category = 'B' THEN value ELSE 0 END) as cat_b FROM table GROUP BY id
            - Unpivot: SELECT id, 'A' as category, cat_a as value FROM table UNION ALL SELECT id, 'B' as category, cat_b as value FROM table
        """
    ),

    "Lookup": (
        r"""
            SQL Lookup Tool: Convert Alteryx lookup operations to SQL JOIN or subquery operations.
            
            Key SQL Operations:
            1. Exact match lookups: INNER JOIN or LEFT JOIN
            2. Fuzzy matching: Use LIKE or string similarity functions
            3. Range lookups: Use BETWEEN or comparison operators
            4. Multiple lookup tables: Chain multiple JOINs
            
            SQL Implementation:
            - Exact lookup: SELECT t1.*, t2.lookup_value FROM table1 t1 LEFT JOIN lookup_table t2 ON t1.key = t2.key
            - Range lookup: SELECT t1.*, t2.category FROM table1 t1 LEFT JOIN range_table t2 ON t1.value BETWEEN t2.min_val AND t2.max_val
            - Multiple lookups: SELECT t1.*, t2.val1, t3.val2 FROM table1 t1 LEFT JOIN lookup1 t2 ON t1.key1 = t2.key1 LEFT JOIN lookup2 t3 ON t1.key2 = t3.key2
    """
    ),

    "Append": (
        r"""
            SQL Append Tool: Convert Alteryx append operations to SQL UNION or INSERT operations.
            
            Key SQL Operations:
            1. Row appending: Use UNION ALL to combine datasets
            2. Column appending: Use CROSS JOIN or UNION with NULLs
            3. Data insertion: Use INSERT INTO statements
            4. Multiple source handling: Chain UNION ALL operations
            
            SQL Implementation:
            - Row append: SELECT * FROM table1 UNION ALL SELECT * FROM table2
            - Column append: SELECT col1, col2, NULL as col3 FROM table1 UNION ALL SELECT NULL as col1, NULL as col2, col3 FROM table2
            - Insert append: INSERT INTO target_table SELECT * FROM source_table
        """
    ),

    "DataValidation": (
        r"""
            SQL Data Validation Tool: Convert Alteryx data validation operations to SQL validation queries.
            
            Key SQL Operations:
            1. Data quality checks: Use CASE statements for validation rules
            2. Constraint validation: Use WHERE clauses with conditions
            3. Statistical validation: Use aggregation functions for data profiling
            4. Error flagging: Use CASE statements to flag invalid records
            
            SQL Implementation:
            - Data quality: SELECT *, CASE WHEN column_name IS NULL OR column_name = '' THEN 'Invalid' ELSE 'Valid' END as validation_status FROM table
            - Constraint check: SELECT * FROM table WHERE value >= 0 AND value <= 100
            - Statistical validation: SELECT COUNT(*) as total, COUNT(CASE WHEN column_name IS NOT NULL THEN 1 END) as non_null_count FROM table
        """
    ),

    "DateTime": (
        r"""
            SQL DateTime Tool: Convert Alteryx datetime operations to SQL date/time functions.
            
            Key SQL Operations:
            1. Date parsing: Use database-specific date parsing functions
            2. Date arithmetic: Use DATE_ADD, DATE_SUB, or arithmetic operators
            3. Date formatting: Use DATE_FORMAT or TO_CHAR functions
            4. Date extraction: Use YEAR(), MONTH(), DAY() functions
            5. Time zone handling: Use CONVERT_TZ or timezone functions
            
            SQL Implementation:
            - Date parsing: STR_TO_DATE(date_string, '%Y-%m-%d')
            - Date arithmetic: DATE_ADD(date_column, INTERVAL 1 DAY)
            - Date formatting: DATE_FORMAT(date_column, '%Y-%m-%d')
            - Date extraction: YEAR(date_column), MONTH(date_column), DAY(date_column)
            - Time zone conversion: CONVERT_TZ(date_column, 'UTC', 'America/New_York')
        """
        ),

    "String": (
        r"""
            SQL String Tool: Convert Alteryx string operations to SQL string functions.
            
            Key SQL Operations:
            1. String concatenation: Use CONCAT() or || operator
            2. String extraction: Use SUBSTRING() or LEFT()/RIGHT()
            3. String replacement: Use REPLACE() or REGEXP_REPLACE()
            4. String case conversion: Use UPPER(), LOWER(), INITCAP()
            5. String pattern matching: Use LIKE or REGEXP functions
            
            SQL Implementation:
            - Concatenation: CONCAT(string1, ' ', string2)
            - Substring: SUBSTRING(column_name, 1, 10)
            - Replacement: REPLACE(column_name, 'old', 'new')
            - Case conversion: UPPER(column_name), LOWER(column_name)
            - Pattern matching: column_name LIKE '%pattern%'
        """
        ),

    "Numeric": (
        r"""
            SQL Numeric Tool: Convert Alteryx numeric operations to SQL mathematical functions.
            
            Key SQL Operations:
            1. Mathematical operations: Use standard arithmetic operators
            2. Rounding functions: Use ROUND(), CEIL(), FLOOR()
            3. Statistical functions: Use AVG(), SUM(), COUNT(), etc.
            4. Random numbers: Use RAND() or database-specific functions
            5. Number formatting: Use CAST() or FORMAT() functions
            
            SQL Implementation:
            - Basic math: column1 + column2, column1 * column2
            - Rounding: ROUND(column_name, 2), CEIL(column_name), FLOOR(column_name)
            - Statistical: AVG(column_name), SUM(column_name), COUNT(*)
            - Random: RAND() * 100
            - Formatting: CAST(column_name AS DECIMAL(10,2))
        """
        ),

    "Conditional": (
        r"""
            SQL Conditional Tool: Convert Alteryx conditional operations to SQL CASE statements.
            
            Key SQL Operations:
            1. Simple conditions: Use CASE WHEN ... THEN ... ELSE ... END
            2. Multiple conditions: Chain multiple WHEN clauses
            3. Nested conditions: Use nested CASE statements
            4. Conditional aggregation: Use CASE within aggregation functions
            
            SQL Implementation:
            - Simple CASE: CASE WHEN condition THEN value1 ELSE value2 END
            - Multiple conditions: CASE WHEN condition1 THEN value1 WHEN condition2 THEN value2 ELSE default_value END
            - Nested CASE: CASE WHEN outer_condition THEN CASE WHEN inner_condition THEN value1 ELSE value2 END ELSE default_value END
            - Conditional aggregation: SUM(CASE WHEN condition THEN amount ELSE 0 END)
        """
        ),

    "Spatial": (
        r"""
            SQL Spatial Tool: Convert Alteryx spatial operations to SQL spatial functions.
            
            Key SQL Operations:
            1. Spatial data types: Use GEOMETRY or GEOGRAPHY data types
            2. Spatial functions: Use ST_* functions for spatial operations
            3. Distance calculations: Use ST_Distance() or similar functions
            4. Spatial relationships: Use ST_Contains(), ST_Intersects(), etc.
            5. Coordinate transformations: Use ST_Transform() functions
            
            SQL Implementation:
            - Distance calculation: ST_Distance(point1, point2)
            - Spatial relationship: ST_Contains(polygon, point)
            - Area calculation: ST_Area(geometry)
            - Buffer creation: ST_Buffer(point, distance)
            - Coordinate transformation: ST_Transform(geometry, new_srid)
        """
        ),

    "Statistical": (
        r"""
            SQL Statistical Tool: Convert Alteryx statistical operations to SQL statistical functions.
            
            Key SQL Operations:
            1. Descriptive statistics: Use AVG(), STDDEV(), VARIANCE()
            2. Percentiles: Use PERCENTILE_CONT() or database-specific functions
            3. Correlation: Use CORR() or calculate manually
            4. Regression: Use database-specific statistical functions
            5. Sampling statistics: Use window functions for rolling statistics
            
            SQL Implementation:
            - Basic statistics: AVG(column_name), STDDEV(column_name), VARIANCE(column_name)
            - Percentiles: PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY column_name)
            - Rolling average: AVG(column_name) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
            - Correlation: CORR(column1, column2)
        """
    ),

    "MachineLearning": (
        r"""
            SQL Machine Learning Tool: Convert Alteryx ML operations to SQL ML functions or data preparation.
            
            Key SQL Operations:
            1. Feature engineering: Use SQL expressions to create features
            2. Data preparation: Use CASE statements for categorical encoding
            3. Scaling/normalization: Use mathematical functions
            4. Model scoring: Use database-specific ML functions
            5. Prediction results: Use CTEs to organize ML workflow
            
            SQL Implementation:
            - Feature creation: CASE WHEN category = 'A' THEN 1 ELSE 0 END as feature_a
            - Data scaling: (value - MIN(value) OVER()) / (MAX(value) OVER() - MIN(value) OVER()) as scaled_value
            - Categorical encoding: CASE category WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 1 END as encoded_category
            - Model scoring: Use database-specific ML functions (e.g., PREDICT() in BigQuery)
        """
        ),

    "Reporting": (
        r"""
            SQL Reporting Tool: Convert Alteryx reporting operations to SQL reporting queries.
            
            Key SQL Operations:
            1. Summary reports: Use GROUP BY with multiple aggregations
            2. Pivot tables: Use conditional aggregation with CASE statements
            3. Time series: Use date functions and window functions
            4. Comparative analysis: Use self-joins or window functions
            5. Ranking: Use ROW_NUMBER(), RANK(), DENSE_RANK()
            
            SQL Implementation:
            - Summary report: SELECT category, COUNT(*), SUM(amount), AVG(amount) FROM table GROUP BY category
            - Pivot report: SELECT year, SUM(CASE WHEN quarter = 'Q1' THEN amount ELSE 0 END) as q1_amount FROM table GROUP BY year
            - Time series: SELECT date, SUM(amount) OVER (ORDER BY date) as running_total FROM table
            - Ranking: SELECT *, ROW_NUMBER() OVER (ORDER BY amount DESC) as rank FROM table
    """
    ),

    "DataQuality": (
        r"""
            SQL Data Quality Tool: Convert Alteryx data quality operations to SQL quality assessment queries.
            
            Key SQL Operations:
            1. Completeness checks: Use COUNT() and COUNT(*) comparisons
            2. Uniqueness checks: Use COUNT() vs COUNT(DISTINCT)
            3. Validity checks: Use CASE statements for business rules
            4. Consistency checks: Use self-joins or window functions
            5. Data profiling: Use aggregation functions for statistics
            
            SQL Implementation:
            - Completeness: SELECT COUNT(*) as total_rows, COUNT(column_name) as non_null_rows FROM table
            - Uniqueness: SELECT COUNT(*) as total, COUNT(DISTINCT column_name) as unique_values FROM table
            - Validity: SELECT COUNT(CASE WHEN column_name BETWEEN min_val AND max_val THEN 1 END) as valid_count FROM table
            - Data profiling: SELECT MIN(column_name), MAX(column_name), AVG(column_name), COUNT(DISTINCT column_name) FROM table
        """
        ),

    "ETL": (
        r"""
            SQL ETL Tool: Convert Alteryx ETL operations to SQL data pipeline queries.
            
            Key SQL Operations:
            1. Extract: Use SELECT statements with appropriate filters
            2. Transform: Use CTEs for complex transformations
            3. Load: Use INSERT, UPDATE, or MERGE statements
            4. Incremental loading: Use date filters or change detection
            5. Error handling: Use transaction control and error logging
            
            SQL Implementation:
            - Extract: SELECT * FROM source_table WHERE last_updated > @last_run_date
            - Transform: WITH transformed_data AS (SELECT *, CASE WHEN condition THEN 'new_value' ELSE original_value END as transformed_column FROM source_data)
            - Load: INSERT INTO target_table SELECT * FROM transformed_data
            - Incremental: MERGE target_table t USING source_table s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.column = s.column WHEN NOT MATCHED THEN INSERT VALUES (s.id, s.column)
        """
        ),

    "Analytics": (
        r"""
            SQL Analytics Tool: Convert Alteryx analytics operations to SQL analytical queries.
            
            Key SQL Operations:
            1. Time series analysis: Use date functions and window functions
            2. Cohort analysis: Use date arithmetic and grouping
            3. Funnel analysis: Use conditional aggregation and window functions
            4. RFM analysis: Use percentile functions and CASE statements
            5. A/B testing: Use statistical functions and hypothesis testing
            
            SQL Implementation:
            - Time series: SELECT date, SUM(amount) OVER (ORDER BY date ROWS BETWEEN 30 PRECEDING AND CURRENT ROW) as rolling_30d FROM table
            - Cohort analysis: SELECT cohort_month, DATEDIFF(activity_date, cohort_date) as days_since_cohort, COUNT(DISTINCT user_id) FROM table GROUP BY cohort_month, days_since_cohort
            - Funnel: SELECT step, COUNT(*) as users, LAG(COUNT(*)) OVER (ORDER BY step) as previous_step FROM funnel_data GROUP BY step
            - RFM: SELECT customer_id, NTILE(5) OVER (ORDER BY recency) as r_score, NTILE(5) OVER (ORDER BY frequency) as f_score, NTILE(5) OVER (ORDER BY monetary) as m_score FROM customer_data
        """
        ),

    "Integration": (
        r"""
            SQL Integration Tool: Convert Alteryx integration operations to SQL data integration queries.
            
            Key SQL Operations:
            1. Data blending: Use UNION, JOIN, or subqueries
            2. API data: Use external table functions or staging tables
            3. Real-time integration: Use change data capture or streaming
            4. Data synchronization: Use MERGE or UPSERT operations
            5. Cross-database queries: Use linked servers or federation
            
            SQL Implementation:
            - Data blending: SELECT * FROM table1 UNION ALL SELECT * FROM table2
            - API integration: INSERT INTO staging_table SELECT * FROM OPENROWSET('API_connection', 'query')
            - Real-time sync: MERGE target_table t USING source_table s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.data = s.data WHEN NOT MATCHED THEN INSERT VALUES (s.id, s.data)
            - Cross-database: SELECT * FROM database1.schema.table1 t1 JOIN database2.schema.table2 t2 ON t1.id = t2.id
        """
        ),

    "Automation": (
        r"""
            SQL Automation Tool: Convert Alteryx automation operations to SQL automated procedures.
            
            Key SQL Operations:
            1. Stored procedures: Use CREATE PROCEDURE for reusable logic
            2. Scheduled jobs: Use database scheduler or external tools
            3. Error handling: Use TRY/CATCH blocks and logging
            4. Parameterization: Use variables and parameters
            5. Dynamic SQL: Use EXEC or sp_executesql for flexible queries
            
            SQL Implementation:
            - Stored procedure: CREATE PROCEDURE process_data @param1 INT AS BEGIN ... END
            - Error handling: BEGIN TRY ... END TRY BEGIN CATCH ... END CATCH
            - Dynamic SQL: EXEC sp_executesql @sql, @params, @param1 = value1
            - Logging: INSERT INTO log_table (procedure_name, start_time, status) VALUES ('process_data', GETDATE(), 'STARTED')
        """
        ),

    "Optimization": (
        r"""
            SQL Optimization Tool: Convert Alteryx optimization operations to SQL performance optimization.
            
            Key SQL Operations:
            1. Query optimization: Use appropriate indexes and hints
            2. Partitioning: Use table partitioning for large datasets
            3. Materialized views: Use indexed views or materialized tables
            4. Query hints: Use OPTION clauses for query optimization
            5. Performance monitoring: Use execution plans and statistics
            
            SQL Implementation:
            - Index hints: SELECT * FROM table WITH (INDEX(index_name))
            - Query hints: SELECT * FROM table OPTION (MAXDOP 4, OPTIMIZE FOR UNKNOWN)
            - Partitioning: SELECT * FROM table WHERE partition_column = 'value'
            - Materialized view: CREATE INDEXED VIEW view_name AS SELECT * FROM table WHERE condition
        """
        ),

    "Security": (
        r"""
            SQL Security Tool: Convert Alteryx security operations to SQL security controls.
            
            Key SQL Operations:
            1. Row-level security: Use security policies and functions
            2. Column-level security: Use encryption or masking functions
            3. Access control: Use GRANT/REVOKE statements
            4. Data masking: Use dynamic data masking or custom functions
            5. Audit logging: Use triggers or change tracking
            
            SQL Implementation:
            - Row-level security: CREATE SECURITY POLICY policy_name ON table_name FOR SELECT USING (user_id = CURRENT_USER)
            - Data masking: SELECT MASK(column_name) as masked_column FROM table
            - Access control: GRANT SELECT ON table_name TO role_name
            - Audit logging: CREATE TRIGGER audit_trigger ON table_name FOR INSERT, UPDATE, DELETE AS INSERT INTO audit_table SELECT GETDATE(), SYSTEM_USER, 'action'
        """
        ),

    "Compliance": (
        r"""
            SQL Compliance Tool: Convert Alteryx compliance operations to SQL compliance queries.
            
            Key SQL Operations:
            1. Data retention: Use date-based filtering and archiving
            2. Privacy controls: Use data masking and anonymization
            3. Audit trails: Use change tracking and logging
            4. Regulatory reporting: Use aggregation and filtering
            5. Data governance: Use metadata and lineage tracking
            
            SQL Implementation:
            - Data retention: DELETE FROM table WHERE created_date < DATE_SUB(NOW(), INTERVAL 7 YEAR)
            - Privacy masking: SELECT CONCAT(LEFT(email, 3), '***@', SUBSTRING_INDEX(email, '@', -1)) as masked_email FROM table
            - Audit trail: SELECT * FROM audit_table WHERE table_name = 'sensitive_table' AND action_date > @start_date
            - Regulatory report: SELECT category, COUNT(*), SUM(amount) FROM transactions WHERE transaction_date BETWEEN @start_date AND @end_date GROUP BY category
        """
    ),

    "Scalability": (
        r"""
            SQL Scalability Tool: Convert Alteryx scalability operations to SQL scalable solutions.
            
            Key SQL Operations:
            1. Partitioning: Use table and index partitioning
            2. Sharding: Use distributed queries across multiple databases
            3. Caching: Use materialized views and indexed views
            4. Parallel processing: Use query hints for parallel execution
            5. Resource management: Use resource governor or similar features
            
            SQL Implementation:
            - Table partitioning: CREATE TABLE partitioned_table (id INT, date_col DATE) PARTITION BY RANGE (YEAR(date_col))
            - Parallel processing: SELECT * FROM large_table OPTION (MAXDOP 8)
            - Materialized view: CREATE MATERIALIZED VIEW cache_view AS SELECT * FROM large_table WHERE condition
            - Resource limits: ALTER RESOURCE GOVERNOR RECONFIGURE
        """
        ),

    "Monitoring": (
        r"""
            SQL Monitoring Tool: Convert Alteryx monitoring operations to SQL monitoring queries.
            
            Key SQL Operations:
            1. Performance monitoring: Use system views and DMVs
            2. Data quality monitoring: Use validation queries and alerts
            3. Job monitoring: Use job history and status tables
            4. Error tracking: Use error logs and exception handling
            5. Health checks: Use diagnostic queries and metrics
            
            SQL Implementation:
            - Performance monitoring: SELECT * FROM sys.dm_exec_query_stats ORDER BY total_elapsed_time DESC
            - Data quality: SELECT COUNT(*) as total_rows, COUNT(CASE WHEN column_name IS NULL THEN 1 END) as null_count FROM table
            - Job monitoring: SELECT job_name, start_time, end_time, status FROM job_history WHERE start_time > @last_check
            - Error tracking: SELECT * FROM error_log WHERE error_date > @start_date ORDER BY error_date DESC
        """
        ),

    "Testing": (
        r"""
            SQL Testing Tool: Convert Alteryx testing operations to SQL testing queries.
            
            Key SQL Operations:
            1. Unit testing: Use test data and expected results
            2. Integration testing: Use end-to-end data flow validation
            3. Performance testing: Use query execution time measurement
            4. Data validation testing: Use business rule validation queries
            5. Regression testing: Use baseline comparison queries
            
            SQL Implementation:
            - Unit test: SELECT CASE WHEN COUNT(*) = expected_count THEN 'PASS' ELSE 'FAIL' END as test_result FROM test_table WHERE condition
            - Integration test: SELECT COUNT(*) as record_count FROM final_table WHERE process_date = @test_date
            - Performance test: SET STATISTICS TIME ON; SELECT * FROM large_table; SET STATISTICS TIME OFF
            - Data validation: SELECT COUNT(*) as invalid_records FROM table WHERE business_rule_condition = FALSE
        """
        ),

    "Documentation": (
        r"""
            SQL Documentation Tool: Convert Alteryx documentation operations to SQL documentation queries.
            
            Key SQL Operations:
            1. Metadata queries: Use system views for table and column information
            2. Data lineage: Use dependency tracking and relationship queries
            3. Schema documentation: Use information schema queries
            4. Business glossary: Use reference tables and lookup queries
            5. Change tracking: Use version control and history queries
            
            SQL Implementation:
            - Metadata: SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'dbo'
            - Data lineage: SELECT * FROM dependency_table WHERE source_table = @table_name
            - Schema info: SELECT t.table_name, c.column_name, c.data_type, c.is_nullable FROM information_schema.tables t JOIN information_schema.columns c ON t.table_name = c.table_name
            - Change history: SELECT * FROM schema_changes WHERE table_name = @table_name ORDER BY change_date DESC
        """
        ),

    "Deployment": (
        r"""
            SQL Deployment Tool: Convert Alteryx deployment operations to SQL deployment procedures.
            
            Key SQL Operations:
            1. Environment management: Use database schemas and configurations
            2. Version control: Use migration scripts and version tracking
            3. Rollback procedures: Use backup and restore operations
            4. Configuration management: Use parameter tables and settings
            5. Release management: Use deployment scripts and validation
            
            SQL Implementation:
            - Environment setup: CREATE SCHEMA production_schema; CREATE SCHEMA staging_schema
            - Version tracking: INSERT INTO version_table (version, deployment_date, description) VALUES ('1.0.0', GETDATE(), 'Initial deployment')
            - Rollback: RESTORE DATABASE database_name FROM backup_file WITH REPLACE
            - Configuration: UPDATE config_table SET value = @new_value WHERE config_key = @key
        """
        ),

    "Maintenance": (
        r"""
            SQL Maintenance Tool: Convert Alteryx maintenance operations to SQL maintenance procedures.
            
            Key SQL Operations:
            1. Index maintenance: Use index rebuild and reorganization
            2. Statistics updates: Use statistics refresh operations
            3. Data archiving: Use partitioning and archival procedures
            4. Cleanup operations: Use data retention and cleanup queries
            5. Health checks: Use diagnostic and monitoring queries
            
            SQL Implementation:
            - Index maintenance: ALTER INDEX ALL ON table_name REBUILD
            - Statistics update: UPDATE STATISTICS table_name
            - Data archiving: INSERT INTO archive_table SELECT * FROM main_table WHERE date_column < @archive_date
            - Cleanup: DELETE FROM log_table WHERE log_date < DATE_SUB(GETDATE(), INTERVAL 90 DAY)
        """
        ),

    "Troubleshooting": (
        r"""
            SQL Troubleshooting Tool: Convert Alteryx troubleshooting operations to SQL diagnostic queries.
            
            Key SQL Operations:
            1. Error diagnosis: Use error logs and exception queries
            2. Performance analysis: Use execution plans and statistics
            3. Data investigation: Use exploratory data analysis queries
            4. Dependency analysis: Use relationship and constraint queries
            5. Root cause analysis: Use historical data and trend analysis
            
            SQL Implementation:
            - Error diagnosis: SELECT * FROM error_log WHERE error_date > @start_date AND error_message LIKE '%specific_error%'
            - Performance analysis: SELECT * FROM sys.dm_exec_query_stats WHERE query_hash = @query_hash
            - Data investigation: SELECT column_name, COUNT(*), COUNT(DISTINCT value) FROM table GROUP BY column_name ORDER BY COUNT(*) DESC
            - Dependency analysis: SELECT * FROM sys.foreign_keys WHERE referenced_table_name = @table_name
        """
        ),

    "Innovation": (
        r"""
            SQL Innovation Tool: Convert Alteryx innovation operations to SQL advanced features.
            
            Key SQL Operations:
            1. Advanced analytics: Use machine learning and statistical functions
            2. Real-time processing: Use streaming and change data capture
            3. Graph analytics: Use recursive CTEs and graph functions
            4. Spatial analytics: Use spatial data types and functions
            5. Time series analysis: Use window functions and temporal features
            
            SQL Implementation:
            - Advanced analytics: SELECT *, PREDICT(model_name, features) as prediction FROM data_table
            - Real-time processing: SELECT * FROM change_table WHERE change_timestamp > @last_check
            - Graph analytics: WITH RECURSIVE graph_path AS (SELECT start_node, end_node, 1 as level FROM edges WHERE start_node = @root UNION ALL SELECT e.start_node, e.end_node, gp.level + 1 FROM edges e JOIN graph_path gp ON e.start_node = gp.end_node WHERE gp.level < 10) SELECT * FROM graph_path
            - Spatial analytics: SELECT *, ST_Distance(point1, point2) as distance FROM spatial_table
        """
        ),

    "Future": (
        r"""
            SQL Future Tool: Convert Alteryx future operations to SQL emerging features.
            
            Key SQL Operations:
            1. Cloud-native features: Use cloud-specific SQL extensions
            2. AI/ML integration: Use built-in machine learning functions
            3. Edge computing: Use lightweight SQL for edge devices
            4. Blockchain integration: Use blockchain data queries
            5. IoT data processing: Use streaming and time-series features
            
            SQL Implementation:
            - Cloud features: SELECT * FROM external_table USING (connection_string)
            - AI integration: SELECT *, AI_PREDICT(model_name, features) as ai_prediction FROM data_table
            - Edge processing: SELECT * FROM edge_table WHERE device_id = @device_id AND timestamp > @last_sync
            - IoT streaming: SELECT * FROM iot_stream WHERE sensor_id = @sensor_id AND reading_time > @start_time
        """
    )
}