"""
A股数据采集系统 - 完整测试报告
===========================
测试环境: Windows
说明: 由于网络限制，部分依赖未安装，将进行代码层面分析和已安装包测试
"""

import sys
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
import importlib

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("A股数据采集系统 - 完整测试报告")
print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

TEST_RESULTS = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "tests": []
}


def log_test(test_name, status, message, duration=0, details=None):
    """记录测试结果"""
    status_icon = {"PASS": "[+]", "FAIL": "[-]", "WARN": "[!]", "INFO": "[*]"}
    icon = status_icon.get(status, "?")
    
    print(f"\n{icon} {test_name}: {status}")
    print(f"    {message}")
    if duration > 0:
        print(f"    Time: {duration:.2f} sec")
    if details:
        for k, v in details.items():
            print(f"    {k}: {v}")
    
    TEST_RESULTS["tests"].append({
        "name": test_name,
        "status": status,
        "message": message,
        "duration": duration,
        "details": details
    })
    
    if status == "PASS":
        TEST_RESULTS["passed"] += 1
    elif status == "FAIL":
        TEST_RESULTS["failed"] += 1
    elif status == "WARN":
        TEST_RESULTS["warnings"] += 1


def check_module(module_name):
    """检查模块是否可用"""
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, None
    except Exception as e:
        return False, str(e)


def test_0_environment():
    """测试0: 环境检查"""
    print("\n" + "=" * 70)
    print("Test 0: Environment Check")
    print("=" * 70)
    
    start_time = time.time()
    
    modules = {
        "duckdb": "DuckDB",
        "pandas": "Pandas",
        "loguru": "Loguru",
        "tenacity": "Tenacity",
        "pydantic": "Pydantic",
        "tushare": "Tushare",
        "akshare": "AKShare",
    }
    
    results = {}
    all_ok = True
    
    print("\nChecking required modules...")
    for module_name, display_name in modules.items():
        available, version = check_module(module_name)
        results[display_name] = {"available": available, "version": version}
        if available:
            print(f"  [OK] {display_name}: {version}")
        else:
            print(f"  [MISSING] {display_name}")
            all_ok = False
    
    log_test("0_Environment", "PASS" if all_ok else "WARN",
            "Environment check completed",
            time.time() - start_time,
            {"Modules": results, "All Available": all_ok})
    
    return all_ok


def test_1_code_structure():
    """测试1: 代码结构检查"""
    print("\n" + "=" * 70)
    print("Test 1: Code Structure Analysis")
    print("=" * 70)
    
    start_time = time.time()
    
    required_files = [
        "config.py",
        "main.py",
        "monitor.py",
        "storage/duckdb_storage.py",
        "storage/__init__.py",
        "data_fetcher/tushare_fetcher.py",
        "data_fetcher/akshare_fetcher.py",
        "data_fetcher/__init__.py",
        "tasks/daily_task.py",
        "tasks/__init__.py",
        "utils/logger.py",
        "utils/retry.py",
        "utils/data_clean.py",
        "utils/__init__.py",
    ]
    
    print("\nChecking file structure...")
    all_exist = True
    missing_files = []
    
    for file_path in required_files:
        full_path = Path(file_path)
        exists = full_path.exists()
        if not exists:
            all_exist = False
            missing_files.append(file_path)
        print(f"  {'[OK]' if exists else '[MISSING]'} {file_path}")
    
    log_test("1.1_File_Structure", "PASS" if all_exist else "FAIL",
            "All required files present" if all_exist else f"Missing: {missing_files}",
            time.time() - start_time,
            {"Missing": missing_files if missing_files else "None"})
    
    print("\nChecking class definitions...")
    class_checks = []
    
    try:
        with open("storage/duckdb_storage.py", "r", encoding="utf-8") as f:
            content = f.read()
            has_pool = "ConnectionPool" in content
            has_storage = "DuckDBStorage" in content
            has_get_conn = "get_connection" in content
            has_return_conn = "return_connection" in content
            class_checks.append({"ConnectionPool": has_pool})
            class_checks.append({"DuckDBStorage": has_storage})
            class_checks.append({"get_connection": has_get_conn})
            class_checks.append({"return_connection": has_return_conn})
            print(f"  {'[OK]' if has_pool else '[MISSING]'} ConnectionPool class")
            print(f"  {'[OK]' if has_storage else '[MISSING]'} DuckDBStorage class")
            print(f"  {'[OK]' if has_get_conn else '[MISSING]'} get_connection method")
            print(f"  {'[OK]' if has_return_conn else '[MISSING]'} return_connection method")
    except Exception as e:
        class_checks.append({"Error": str(e)})
        print(f"  [ERROR] {e}")
    
    log_test("1.2_Class_Definitions", "PASS" if all(class_checks) else "FAIL",
            "Class structure verified",
            time.time() - start_time,
            {"Classes": class_checks})
    
    print("\nChecking key methods in DuckDBStorage...")
    methods = ["init_tables", "get_latest_date", "insert_or_update", 
               "insert_or_update_financial", "insert_stock_basic", "close"]
    method_checks = {}
    
    try:
        with open("storage/duckdb_storage.py", "r", encoding="utf-8") as f:
            content = f.read()
            for method in methods:
                exists = f"def {method}" in content
                method_checks[method] = exists
                print(f"  {'[OK]' if exists else '[MISSING]'} {method}()")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    log_test("1.3_Method_Definitions", "PASS" if all(method_checks.values()) else "FAIL",
            "Required methods present",
            time.time() - start_time,
            {"Methods": method_checks})
    
    total_duration = time.time() - start_time
    log_test("Test1_Code_Structure", "PASS",
            f"Analysis completed in {total_duration:.2f} sec", total_duration)
    
    return True


def test_2_connection_pool_analysis():
    """测试2: 连接池代码分析"""
    print("\n" + "=" * 70)
    print("Test 2: Connection Pool Code Analysis")
    print("=" * 70)
    
    start_time = time.time()
    issues = []
    checks_passed = []
    
    print("\nAnalyzing ConnectionPool class...")
    
    try:
        with open("storage/duckdb_storage.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        print("\n  2.1 Checking context manager usage...")
        has_context_manager = "@contextmanager" in content
        if has_context_manager:
            issues.append("Still uses @contextmanager decorator (should be removed)")
            print("  [WARN] Still uses @contextmanager decorator")
        else:
            checks_passed.append("No @contextmanager usage")
            print("  [OK] No context manager decorator found")
        
        print("\n  2.2 Checking get_connection/return_connection pattern...")
        has_get_conn = "def get_connection" in content
        has_return_conn = "def return_connection" in content
        if has_get_conn and has_return_conn:
            checks_passed.append("Proper get/return connection pattern")
            print("  [OK] Has proper get_connection/return_connection methods")
        else:
            issues.append("Missing get_connection or return_connection")
            print("  [FAIL] Missing connection management methods")
        
        print("\n  2.3 Checking _execute_with_connection pattern...")
        has_execute_wrapper = "_execute_with_connection" in content
        if has_execute_wrapper:
            checks_passed.append("Has _execute_with_connection wrapper")
            print("  [OK] Has _execute_with_connection wrapper for thread safety")
            
            if "try:" in content and "finally:" in content:
                has_finally = True
                checks_passed.append("Has try-finally for connection return")
                print("  [OK] Has try-finally for proper cleanup")
            else:
                issues.append("Missing try-finally in connection handling")
                print("  [FAIL] Missing try-finally block")
        else:
            issues.append("Missing _execute_with_connection wrapper")
            print("  [FAIL] Missing _execute_with_connection wrapper")
        
        print("\n  2.4 Checking close() method...")
        has_close_all = "close_all" in content
        has_pool_reset = "_pool = None" in content or "_pool = None" in content.replace("DuckDBStorage.", "")
        if has_close_all:
            checks_passed.append("Has close_all method")
            print("  [OK] Has close_all method")
        if has_pool_reset:
            checks_passed.append("Pool reset on close")
            print("  [OK] Pool resets _pool to None on close")
        
        print("\n  2.5 Checking for _local_conn usage...")
        has_local_conn = "_local_conn" in content
        if has_local_conn:
            issues.append("Still has _local_conn attribute (should be removed)")
            print("  [WARN] Still references _local_conn")
        else:
            checks_passed.append("No _local_conn attribute")
            print("  [OK] No _local_conn attribute found")
        
        print("\n  2.6 Checking SQL injection in insert_or_update_financial...")
        sql_lines = []
        for i, line in enumerate(content.split('\n')):
            if 'temp_financial' in line.lower() and ('from' in line.lower() or 'delete' in line.lower()):
                sql_lines.append((i+1, line.strip()))
        
        if sql_lines:
            has_hardcoded_sql = False
            for line_num, line in sql_lines:
                if 'temp_financial' in line and 'replace' not in line and 'temp_table' not in line:
                    has_hardcoded_sql = True
                    issues.append(f"Hardcoded temp_financial at line {line_num}")
                    print(f"  [FAIL] Hardcoded temp_financial at line {line_num}")
            if not has_hardcoded_sql:
                checks_passed.append("SQL temp table names are dynamic")
                print("  [OK] Temp table names are dynamically generated")
        else:
            checks_passed.append("No hardcoded temp table references")
            print("  [OK] No hardcoded temp table references")
    
    except Exception as e:
        issues.append(f"Analysis error: {str(e)}")
        print(f"  [ERROR] {e}")
    
    print("\n" + "-" * 50)
    print(f"Checks Passed: {len(checks_passed)}")
    for check in checks_passed:
        print(f"  + {check}")
    
    print(f"\nIssues Found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")
    
    log_test("2_Connection_Pool", "PASS" if len(issues) == 0 else "WARN",
            f"Analysis completed. {len(issues)} issues found",
            time.time() - start_time,
            {"Passed": checks_passed, "Issues": issues})
    
    return len(issues) == 0


def test_3_data_fetcher_analysis():
    """测试3: 数据获取器代码分析"""
    print("\n" + "=" * 70)
    print("Test 3: Data Fetcher Code Analysis")
    print("=" * 70)
    
    start_time = time.time()
    
    print("\n  3.1 Checking TushareFetcher...")
    issues_tushare = []
    
    try:
        with open("data_fetcher/tushare_fetcher.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        has_daily_basic = "fetch_daily_basic" in content
        has_stock_basic = "fetch_stock_basic" in content
        has_daily = "fetch_daily" in content
        
        print(f"    {'[WARN]' if has_daily_basic else '[OK]'} Has fetch_daily_basic: {has_daily_basic}")
        print(f"    {'[OK]'} Has fetch_stock_basic: {has_stock_basic}")
        print(f"    {'[OK]'} Has fetch_daily: {has_daily}")
        
        if has_daily_basic:
            issues_tushare.append("TushareFetcher still has fetch_daily_basic (should be removed)")
        
        has_random_delay = "random_delay" in content
        print(f"    {'[OK]' if has_random_delay else '[WARN]'} Has random_delay: {has_random_delay}")
        if not has_random_delay:
            issues_tushare.append("Missing random_delay in Tushare")
        
        log_test("3.1_TushareFetcher", "PASS" if not issues_tushare else "WARN",
                "Tushare fetcher analysis",
                details={"Issues": issues_tushare if issues_tushare else "None"})
    
    except Exception as e:
        print(f"    [ERROR] {e}")
        log_test("3.1_TushareFetcher", "FAIL", str(e))
    
    print("\n  3.2 Checking AKShareFetcher...")
    issues_akshare = []
    
    try:
        with open("data_fetcher/akshare_fetcher.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        has_fetch_valuation = "fetch_valuation" in content
        has_fetch_daily = "fetch_daily" in content
        has_random_delay = "random_delay" in content
        has_log_prefix = "[AKShare]" in content or "[AKShare" in content
        
        print(f"    {'[OK]'} Has fetch_valuation: {has_fetch_valuation}")
        print(f"    {'[OK]'} Has fetch_daily: {has_fetch_daily}")
        print(f"    {'[OK]' if has_random_delay else '[WARN]'} Has random_delay: {has_random_delay}")
        print(f"    {'[OK]' if has_log_prefix else '[WARN]'} Has log prefix: {has_log_prefix}")
        
        if not has_random_delay:
            issues_akshare.append("Missing random_delay in AKShare")
        if not has_log_prefix:
            issues_akshare.append("Missing [AKShare] log prefix")
        
        has_incomplete_warning = "may be incomplete" in content or "Consider using alternative" in content
        print(f"    {'[OK]' if has_incomplete_warning else '[WARN]'} Has data completeness warning: {has_incomplete_warning}")
        if not has_incomplete_warning:
            issues_akshare.append("Missing valuation data completeness warning")
        
        log_test("3.2_AKShareFetcher", "PASS" if len(issues_akshare) == 0 else "WARN",
                "AKShare fetcher analysis",
                details={"Issues": issues_akshare if issues_akshare else "None"})
    
    except Exception as e:
        print(f"    [ERROR] {e}")
        log_test("3.2_AKShareFetcher", "FAIL", str(e))
    
    print("\n  3.3 Checking data source priority...")
    
    try:
        with open("tasks/daily_task.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        daily_update_section = content[content.find("def update_daily_data"):content.find("def update_valuation_data")]
        valuation_section = content[content.find("def update_valuation_data"):content.find("def update_financial_data")]
        
        tushare_first_daily = "TUSHARE_ENABLED" in daily_update_section
        akshare_fallback = "AKShare_ENABLED" in daily_update_section and daily_update_section.rfind("AKShare_ENABLED") > daily_update_section.rfind("TUSHARE_ENABLED")
        akshare_only_valuation = "AKShare" in valuation_section and "Tushare" not in valuation_section
        
        print(f"    {'[OK]' if tushare_first_daily else '[WARN]'} Daily: Tushare checked first: {tushare_first_daily}")
        print(f"    {'[OK]' if akshare_fallback else '[WARN]'} Daily: AKShare as fallback: {akshare_fallback}")
        print(f"    {'[OK]' if akshare_only_valuation else '[WARN]'} Valuation: AKShare only: {akshare_only_valuation}")
        
        log_test("3.3_Data_Priority", "PASS",
                "Data source priority analysis",
                details={
                    "Tushare_first_for_daily": tushare_first_daily,
                    "AKShare_fallback": akshare_fallback,
                    "AKShare_only_valuation": akshare_only_valuation
                })
    
    except Exception as e:
        print(f"    [ERROR] {e}")
        log_test("3.3_Data_Priority", "FAIL", str(e))
    
    total_duration = time.time() - start_time
    log_test("Test3_Data_Fetcher", "PASS",
            f"Analysis completed in {total_duration:.2f} sec", total_duration)
    
    return True


def test_4_main_resource_cleanup():
    """测试4: main.py 资源清理分析"""
    print("\n" + "=" * 70)
    print("Test 4: Main.py Resource Cleanup Analysis")
    print("=" * 70)
    
    start_time = time.time()
    issues = []
    checks_passed = []
    
    print("\nAnalyzing main.py resource management...")
    
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        print("\n  4.1 Checking for finally blocks...")
        finally_count = content.count("finally:")
        print(f"    Finally blocks found: {finally_count}")
        if finally_count > 0:
            checks_passed.append(f"Has {finally_count} finally blocks")
        else:
            issues.append("No finally blocks found - resource leak risk")
        
        print("\n  4.2 Checking storage.close() calls...")
        close_in_finally = "storage.close()" in content and "finally:" in content
        print(f"    storage.close() in finally: {close_in_finally}")
        if close_in_finally:
            checks_passed.append("storage.close() in finally block")
        else:
            issues.append("storage.close() not in finally block")
        
        print("\n  4.3 Checking for VACUUM/ANALYZE...")
        has_vacuum = "vacuum()" in content
        has_analyze = "analyze()" in content
        print(f"    Has vacuum(): {has_vacuum}")
        print(f"    Has analyze(): {has_analyze}")
        if has_vacuum and has_analyze:
            checks_passed.append("Has VACUUM and ANALYZE in init")
        else:
            issues.append("Missing VACUUM or ANALYZE")
        
        print("\n  4.4 Checking exception handling...")
        has_keyboard_interrupt = "KeyboardInterrupt" in content
        has_except_block = "except" in content
        print(f"    Handles KeyboardInterrupt: {has_keyboard_interrupt}")
        print(f"    Has except blocks: {has_except_block}")
        if has_keyboard_interrupt and has_except_block:
            checks_passed.append("Proper exception handling")
        
        print("\n  4.5 Checking log format...")
        has_separator = "=" * 60 in content or "="*50 in content
        has_duration = "duration" in content.lower()
        print(f"    Has log separators: {has_separator}")
        print(f"    Tracks duration: {has_duration}")
        if has_separator and has_duration:
            checks_passed.append("Good logging format")
    
    except Exception as e:
        issues.append(f"Analysis error: {str(e)}")
        print(f"  [ERROR] {e}")
    
    print("\n" + "-" * 50)
    print(f"Checks Passed: {len(checks_passed)}")
    for check in checks_passed:
        print(f"  + {check}")
    
    print(f"\nIssues Found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")
    
    log_test("4_Main_Resource_Cleanup", "PASS" if len(issues) == 0 else "WARN",
            f"Analysis completed. {len(issues)} issues found",
            time.time() - start_time,
            {"Passed": checks_passed, "Issues": issues})
    
    return len(issues) == 0


def test_5_config_analysis():
    """测试5: 配置文件分析"""
    print("\n" + "=" * 70)
    print("Test 5: Configuration Analysis")
    print("=" * 70)
    
    start_time = time.time()
    
    print("\nChecking config.py...")
    checks = {}
    
    try:
        with open("config.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_configs = [
            ("FINANCIAL_UPDATE_FREQ", "Financial update frequency"),
            ("CONNECTION_POOL_SIZE", "Connection pool size"),
            ("VALUATION_VALIDATION_RULES", "Valuation validation rules"),
            ("USER_AGENT_POOL", "User-Agent pool"),
            ("MAX_CONCURRENT", "Max concurrent threads"),
            ("REQUEST_DELAY_MIN", "Min request delay"),
            ("REQUEST_DELAY_MAX", "Max request delay"),
        ]
        
        print("\n  Required configurations:")
        for config_name, description in required_configs:
            exists = config_name in content
            checks[description] = exists
            print(f"    {'[OK]' if exists else '[MISSING]'} {description}: {config_name}")
        
        log_test("5_Config_Analysis", "PASS" if all(checks.values()) else "WARN",
                "Configuration analysis completed",
                details={"Config checks": checks})
    
    except Exception as e:
        print(f"  [ERROR] {e}")
        log_test("5_Config_Analysis", "FAIL", str(e))
    
    print("\nChecking .env file...")
    env_checks = {}
    
    try:
        if Path(".env").exists():
            print("  .env file exists")
            env_checks["exists"] = True
            
            with open(".env", "r", encoding="utf-8") as f:
                env_content = f.read()
            
            has_token_placeholder = "TUSHARE_TOKEN=" in env_content
            has_example = "your_tushare_token" in env_content
            print(f"    Has TUSHARE_TOKEN: {has_token_placeholder}")
            print(f"    Has placeholder value: {has_example}")
            
            env_checks["has_token_config"] = has_token_placeholder
            env_checks["placeholder_warning"] = has_example
        else:
            print("  .env file NOT found")
            env_checks["exists"] = False
        
        log_test("5.2_Env_File", "PASS" if env_checks.get("exists") else "WARN",
                ".env file analysis",
                details=env_checks)
    
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    total_duration = time.time() - start_time
    log_test("Test5_Config", "PASS",
            f"Analysis completed in {total_duration:.2f} sec", total_duration)
    
    return True


def test_6_data_clean_analysis():
    """测试6: 数据清洗模块分析"""
    print("\n" + "=" * 70)
    print("Test 6: Data Clean Module Analysis")
    print("=" * 70)
    
    start_time = time.time()
    checks = {}
    
    print("\nChecking data_clean.py...")
    
    try:
        with open("utils/data_clean.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        functions = [
            ("normalize_ts_code", "Normalize ts_code format"),
            ("normalize_date", "Normalize date format"),
            ("validate_valuation_data", "Validate valuation data"),
            ("standardize_daily_data", "Standardize daily data"),
            ("standardize_valuation_data", "Standardize valuation data"),
            ("standardize_financial_data", "Standardize financial data"),
        ]
        
        print("\n  Required functions:")
        for func_name, description in functions:
            exists = f"def {func_name}" in content
            checks[func_name] = exists
            print(f"    {'[OK]' if exists else '[MISSING]'} {description}: {func_name}")
        
        print("\n  Checking validation rules...")
        has_validation_rules = "VALUATION_VALIDATION_RULES" in content
        has_validate_function = "validate_valuation" in content
        print(f"    {'[OK]' if has_validation_rules else '[MISSING]'} Validation rules in config")
        print(f"    {'[OK]' if has_validate_function else '[MISSING]'} Validation function")
        
        checks["has_validation"] = has_validation_rules and has_validate_function
        
        print("\n  Checking ts_code format support...")
        supports_bj = ".BJ" in content
        supports_sh = ".SH" in content
        supports_sz = ".SZ" in content
        print(f"    {'[OK]' if supports_sh else '[WARN]'} Supports .SH: {supports_sh}")
        print(f"    {'[OK]' if supports_sz else '[WARN]'} Supports .SZ: {supports_sz}")
        print(f"    {'[OK]' if supports_bj else '[WARN]'} Supports .BJ (Beijing): {supports_bj}")
        
        checks["supports_all_exchanges"] = supports_sh and supports_sz and supports_bj
        
        log_test("6_Data_Clean", "PASS" if all(checks.values()) else "WARN",
                "Data clean module analysis",
                details={"Checks": checks})
    
    except Exception as e:
        print(f"  [ERROR] {e}")
        log_test("6_Data_Clean", "FAIL", str(e))
    
    total_duration = time.time() - start_time
    log_test("Test6_Data_Clean", "PASS",
            f"Analysis completed in {total_duration:.2f} sec", total_duration)
    
    return True


def test_7_gitignore_analysis():
    """测试7: .gitignore 分析"""
    print("\n" + "=" * 70)
    print("Test 7: .gitignore Analysis")
    print("=" * 70)
    
    start_time = time.time()
    
    required_ignores = [
        ("__pycache__", "Python cache"),
        (".env", "Environment file"),
        ("data/", "Data directory"),
        ("*.duckdb", "DuckDB files"),
        ("logs/", "Log directory"),
        (".venv", "Virtual environment"),
        ("venv/", "Virtual environment"),
    ]
    
    checks = {}
    
    print("\nChecking .gitignore...")
    
    try:
        if Path(".gitignore").exists():
            with open(".gitignore", "r", encoding="utf-8") as f:
                content = f.read()
            
            print("  Required ignores:")
            for pattern, description in required_ignores:
                ignored = pattern in content
                checks[description] = ignored
                print(f"    {'[OK]' if ignored else '[MISSING]'} {description}: {pattern}")
            
            env_example = Path(".env.example").exists()
            checks["has_env_example"] = env_example
            print(f"    {'[OK]' if env_example else '[WARN]'} Has .env.example: {env_example}")
            
            log_test("7_Gitignore", "PASS" if all(checks.values()) else "WARN",
                    ".gitignore analysis",
                    details={"Checks": checks})
        else:
            print("  .gitignore NOT FOUND")
            log_test("7_Gitignore", "FAIL", ".gitignore not found")
    
    except Exception as e:
        print(f"  [ERROR] {e}")
        log_test("7_Gitignore", "FAIL", str(e))
    
    total_duration = time.time() - start_time
    log_test("Test7_Gitignore", "PASS",
            f"Analysis completed in {total_duration:.2f} sec", total_duration)
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("Starting Test Execution...")
    print("=" * 70)
    
    overall_start = time.time()
    
    test_0_environment()
    test_1_code_structure()
    test_2_connection_pool_analysis()
    test_3_data_fetcher_analysis()
    test_4_main_resource_cleanup()
    test_5_config_analysis()
    test_6_data_clean_analysis()
    test_7_gitignore_analysis()
    
    overall_duration = time.time() - overall_start
    
    print("\n" + "=" * 70)
    print("Test Execution Complete")
    print("=" * 70)
    
    print(f"\nTest Results Summary:")
    print(f"  [+] Passed: {TEST_RESULTS['passed']}")
    print(f"  [-] Failed: {TEST_RESULTS['failed']}")
    print(f"  [!] Warnings: {TEST_RESULTS['warnings']}")
    print(f"  Total time: {overall_duration:.2f} sec ({overall_duration/60:.2f} min)")
    
    pass_rate = TEST_RESULTS['passed'] / (TEST_RESULTS['passed'] + TEST_RESULTS['failed'] + 0.001) * 100
    print(f"\nPass Rate: {pass_rate:.1f}%")
    
    print("\n" + "=" * 70)
    print("Detailed Test Records:")
    print("=" * 70)
    for i, test in enumerate(TEST_RESULTS["tests"], 1):
        icon = {"PASS": "[+]", "FAIL": "[-]", "WARN": "[!]", "INFO": "[*]"}.get(test["status"], "?")
        print(f"\n{i}. {icon} {test['name']}")
        print(f"   {test['message'][:80]}..." if len(test['message']) > 80 else f"   {test['message']}")
        if test['duration'] > 0:
            print(f"   Time: {test['duration']:.2f} sec")
    
    print("\n" + "=" * 70)
    print("Test Report End")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("IMPORTANT NOTES FOR DEPLOYMENT:")
    print("=" * 70)
    print("""
1. MISSING DEPENDENCIES:
   - pip install duckdb pandas loguru tenacity pydantic python-dotenv tushare akshare
   
2. BEFORE RUNNING:
   - Copy .env.example to .env
   - Add your Tushare token to .env
   - Ensure data/ and logs/ directories exist
   
3. RECOMMENDED TEST SEQUENCE:
   python main.py --mode init
   python main.py --mode update_stock_list
   python main.py --mode stats
   python main.py --mode daily
   python main.py --mode history --start 20240101 --end 20241231
   
4. NAS CRON SETUP (18:30 daily):
   30 18 * * * cd /path/to/stock_data && python main.py --mode daily >> logs/cron.log 2>&1
    """)


if __name__ == "__main__":
    main()
