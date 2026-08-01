import re
from src.error import InvalidSQLGenerated

ALLOWED_TABLES = {
    "equipment",
    "datasets"
}

FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE"
}

FORBIDDEN_FUNCTIONS = {
    "pg_sleep",
    "version",
    "current_user",
    "session_user",
    "pg_read_file",
    "copy"
}

def validate_select(sql:str):
    if not sql.upper().startswith("SELECT"):
        raise InvalidSQLGenerated(
            "Only selected queries are allowed"
        )

def validate_single_statement(sql:str):
    sql = sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1]
    if ";" in sql:
        raise InvalidSQLGenerated(
            "Multiple SQL statments are not allowed."
        )

def validate_comments(sql:str):
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise InvalidSQLGenerated(
            "SQL comments are not allowed."
        )

def validate_keywords(sql : str):
    sql_upper = sql.upper()

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b",sql_upper):
            raise InvalidSQLGenerated(
                f"Forbidden keyword detected: {keyword}"
            )

def validate_functions(sql : str):

    sql_lower = sql.lower()
    for func in FORBIDDEN_FUNCTIONS:
        if re.search(rf"\b{func}\s*\(",sql_lower):
            raise InvalidSQLGenerated(
                f"Forbidden function detected: {func}"
            )

def validate_tables(sql : str):

    tables = re.findall(
        r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        sql,
        re.IGNORECASE,
    )
    for table in tables:
        if table.lower() not in ALLOWED_TABLES:
            raise InvalidSQLGenerated(
                f"Table '{table} is not allowed."
            )


def clean_sql(sql:str)->str:
    sql = clean_text(sql)
    sql = sql.replace("```sql","")
    sql = sql.replace("```", "")

    sql = sql.strip()
    sql = re.sub(r"\s+"," ",sql)

    return sql

def validate_sql(sql: str):
    validate_select(sql)
    validate_single_statement(sql)
    validate_comments(sql)
    validate_keywords(sql)
    validate_functions(sql)
    validate_tables(sql)



def clean_text(content):

    if isinstance(content,str):
        return content.strip()
    
    if isinstance(content,list):
        content = "".join(block["text"]
                          for block in content
                          if isinstance(block,dict) and block.get("type") == "text")
        return content.strip()

    return str(content).strip()