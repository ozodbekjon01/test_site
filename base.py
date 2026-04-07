import sqlite3


# conn = sqlite3.connect('database.db')
# c = conn.cursor()

with sqlite3.connect('database.db') as conn:
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            class_number integer NOT NULL,
            role TEXT NOT NULL,
            school_id INTEGER NOT NULL,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
    ''')
    
    c.execute(""" create table if not exists schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    ) """)
    
    
    
    c.execute(""" create table if not exists test_to_schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER NOT NULL,
        school_id INTEGER NOT NULL,
        FOREIGN KEY (test_id) REFERENCES tests(id),
        FOREIGN KEY (school_id) REFERENCES schools(id)
        ) """)
    
    
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            duration INTEGER NOT NULL,
            description TEXT NOT NULL,
            test_class INTEGER NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL
        )
    ''')
    
    c.execute(""" create table if not exists questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        test_id INTEGER NOT NULL,
        FOREIGN KEY (test_id) REFERENCES tests(id)
    ) """)
    
    c.execute(""" create table if not exists answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        question_id INTEGER NOT NULL,
        is_correct BOOLEAN,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    ) """)
    
    c.execute(""" CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,          
        test_id INTEGER NOT NULL,          
        score INTEGER DEFAULT 0,           
        max_score INTEGER DEFAULT 0,      
        start_time DATETIME,              
        end_time DATETIME,
        completed BOOLEAN DEFAULT 0,                   
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (test_id) REFERENCES tests(id)
    ); """)
    
    c.execute(""" CREATE TABLE IF NOT EXISTS user_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        result_id INTEGER NOT NULL,        -- test_results jadvalidagi ID
        question_id INTEGER NOT NULL,      -- savol identifikatori
        answer_id INTEGER,                 -- foydalanuvchi tanlagan javob
        FOREIGN KEY (result_id) REFERENCES test_results(id),
        FOREIGN KEY (question_id) REFERENCES questions(id),
        FOREIGN KEY (answer_id) REFERENCES answers(id)
    ); """)
    
    
    
    admin_login = 'admin'
    admin_password = 'admin123'
    c.execute(""" insert into users (full_name, username, password, class_number, role, school_id)
                  values (?, ?, ?, ?, ?, ?) """, ('Admin User', admin_login, admin_password, 0, 'admin', 1))
    
    c.execute(""" insert into schools (name) values (?) """, ('BUXOR TUMANI 8-MAKTAB',))
    
    
    
    
    
    
    conn.commit()
    
    
    