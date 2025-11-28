#!/usr/bin/env python3
"""
数据库内容查看脚本
用于展示 todolist.db 数据库中所有表的内容
"""

import sqlite3
import os
from datetime import datetime

def connect_db():
    """连接数据库"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'todolist.db')
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None
    return sqlite3.connect(db_path)

def print_separator(title="", width=80):
    """打印分隔线"""
    if title:
        title = f" {title} "
        padding = (width - len(title)) // 2
        print("=" * padding + title + "=" * (width - padding - len(title)))
    else:
        print("=" * width)

def print_table_header(columns):
    """打印表头"""
    header = " | ".join(f"{col:15}" for col in columns)
    print(header)
    print("-" * len(header))

def format_value(value, max_length=15):
    """格式化值，限制长度"""
    if value is None:
        return "NULL"
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[:max_length-3] + "..."
    return str_value

def show_table_info(cursor, table_name):
    """显示表的基本信息"""
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    
    # 获取记录数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    
    print(f"\n📋 表名: {table_name}")
    print(f"📊 记录数: {count}")
    
    if columns_info:
        print("🏗️  表结构:")
        for col in columns_info:
            col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
            pk_mark = " (主键)" if pk else ""
            null_mark = " NOT NULL" if not_null else ""
            default_mark = f" DEFAULT {default}" if default else ""
            print(f"   • {col_name}: {col_type}{pk_mark}{null_mark}{default_mark}")

def show_table_data(cursor, table_name, limit=50):
    """显示表数据"""
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()
    
    if not rows:
        print("📭 表中暂无数据")
        return
    
    # 获取列名
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"\n📄 数据内容 (最多显示 {limit} 条):")
    print_table_header(columns)
    
    for row in rows:
        formatted_row = [format_value(value) for value in row]
        print(" | ".join(f"{val:15}" for val in formatted_row))

def show_relationships(cursor):
    """显示表之间的关系"""
    print_separator("表关系分析")
    
    # 用户-项目组关系
    cursor.execute("""
        SELECT u.username, pg.name as group_name, ug.joined_at
        FROM user_groups ug
        JOIN users u ON ug.user_id = u.id
        JOIN project_groups pg ON ug.group_id = pg.id
        ORDER BY ug.joined_at DESC
    """)
    user_groups = cursor.fetchall()
    
    if user_groups:
        print("\n👥 用户-项目组关系:")
        print_table_header(["用户名", "项目组", "加入时间"])
        for row in user_groups:
            formatted_row = [format_value(value, 20) for value in row]
            print(" | ".join(f"{val:20}" for val in formatted_row))
    
    # 项目组领导关系
    cursor.execute("""
        SELECT pg.name as group_name, u.username as leader, pg.project_title
        FROM project_groups pg
        JOIN users u ON pg.leader_id = u.id
        ORDER BY pg.name
    """)
    group_leaders = cursor.fetchall()
    
    if group_leaders:
        print("\n👑 项目组领导:")
        print_table_header(["项目组", "组长", "项目标题"])
        for row in group_leaders:
            formatted_row = [format_value(value, 25) for value in row]
            print(" | ".join(f"{val:25}" for val in formatted_row))

def show_statistics(cursor):
    """显示统计信息"""
    print_separator("数据统计")
    
    # 基本统计
    stats = {}
    tables = ['users', 'project_groups', 'user_groups', 'group_messages', 'message_read_status']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cursor.fetchone()[0]
    
    print("\n📈 数据统计:")
    for table, count in stats.items():
        print(f"   • {table}: {count} 条记录")
    
    # 活跃用户统计
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = cursor.fetchone()[0]
    print(f"   • 活跃用户: {active_users} 个")
    
    # 活跃项目组统计
    cursor.execute("SELECT COUNT(*) FROM project_groups WHERE is_active = 1")
    active_groups = cursor.fetchone()[0]
    print(f"   • 活跃项目组: {active_groups} 个")

def main():
    """主函数"""
    print_separator("ToDoList 数据库内容查看器")
    print(f"🕒 查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("❌ 数据库中没有找到任何表")
            return
        
        # 显示统计信息
        show_statistics(cursor)
        
        # 显示每个表的详细信息
        for table_name in tables:
            print_separator(f"表: {table_name}")
            show_table_info(cursor, table_name)
            show_table_data(cursor, table_name)
        
        # 显示关系分析
        show_relationships(cursor)
        
        print_separator("查看完成")
        print("✅ 数据库内容展示完毕")
        
    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
    except Exception as e:
        print(f"❌ 程序错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()