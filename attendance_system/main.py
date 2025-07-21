import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QTableWidgetItem
from attendance import Ui_Dialog
import pymysql
from datetime import date

class AttendanceApp(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.connect_buttons()
        self.connect_db()

    def connect_buttons(self):
        self.pushButton.clicked.connect(self.mark_attendance)      # ENTER
        self.pushButton_2.clicked.connect(self.register_student)   # REGISTER
        self.pushButton_3.clicked.connect(self.view_attendance)    # VIEW ATTENDANCE

    def connect_db(self):
        self.conn = pymysql.connect(
            host="localhost",
            user="root",
            password="your_password_here",  # Change this before running
            database="attendance_db"
        )
        self.cursor = self.conn.cursor()

    def mark_attendance(self):
        reg_no = self.register_no.text()
        if not reg_no:
            QMessageBox.warning(self, "Input Error", "Please enter your register number.")
            return

        # Find student
        self.cursor.execute("SELECT id, name FROM students WHERE register_no = %s", (reg_no,))
        student = self.cursor.fetchone()

        if student:
            student_id, name = student

            # Check if attendance already marked today
            today = date.today()
            self.cursor.execute("SELECT * FROM attendance WHERE student_id = %s AND date = %s", (student_id, today))
            if self.cursor.fetchone():
                QMessageBox.information(self, "Already Marked", f"Attendance already marked for {name} today.")
                return

            # Mark attendance
            self.cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)",
                                (student_id, today, "Present"))
            self.conn.commit()
            QMessageBox.information(self, "Success", f"Attendance marked successfully for {name}.")
        else:
            QMessageBox.warning(self, "Not Found", "Register number not found. Please register first.")

    def register_student(self):
        reg_no = self.newregister_no.text()
        name = self.name.text()
        if not reg_no or not name:
            QMessageBox.warning(self, "Input Error", "Please enter name and register number.")
            return

        try:
            self.cursor.execute("INSERT INTO students (name, register_no) VALUES (%s, %s)", (name, reg_no))
            self.conn.commit()
            QMessageBox.information(self, "Success", "Student registered successfully.")
            self.newregister_no.clear()
            self.name.clear()
        except pymysql.err.IntegrityError:
            QMessageBox.warning(self, "Error", "Register number already exists.")

    def view_attendance(self):
        try:
        # Get total number of distinct attendance days
            self.cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
            total_days = self.cursor.fetchone()[0]
            if total_days == 0:
                total_days = 1  # Prevent division by zero

        # Get attendance summary per student
            self.cursor.execute("""
                SELECT s.name, s.register_no,
                       COUNT(a.id) AS days_present
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.status = 'Present'
                GROUP BY s.id, s.name, s.register_no
            """)
            results = self.cursor.fetchall()

        # Populate table
            self.attendanceTable.setRowCount(0)
            self.attendanceTable.setColumnCount(4)
            self.attendanceTable.setHorizontalHeaderLabels(["Name", "Register No", "Days Present", "Attendance %"])

            for row_num, row_data in enumerate(results):
                name, reg_no, present = row_data
                percentage = round((present / total_days) * 100, 2)

                self.attendanceTable.insertRow(row_num)
                self.attendanceTable.setItem(row_num, 0, QTableWidgetItem(str(name)))
                self.attendanceTable.setItem(row_num, 1, QTableWidgetItem(str(reg_no)))
                self.attendanceTable.setItem(row_num, 2, QTableWidgetItem(str(present)))
                self.attendanceTable.setItem(row_num, 3, QTableWidgetItem(str(percentage)))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Something went wrong:\n{str(e)}")
            print("Error in view_attendance():", e)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app.exec_())
