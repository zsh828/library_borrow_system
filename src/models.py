from datetime import date, timedelta
from typing import Optional


class Book:
    """图书模型"""
    def __init__(self, isbn: str, title: str, author: str):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.is_available = True  # 默认在馆

    def __repr__(self):
        return f"Book(isbn='{self.isbn}', title='{self.title}', author='{self.author}')"


class Borrower:
    """借阅人模型"""
    MAX_BORROW_LIMIT = 5

    def __init__(self, borrower_id: str, name: str):
        self.borrower_id = borrower_id
        self.name = name
        self.current_borrow_count = 0  # 当前已借数量

    def can_borrow(self) -> bool:
        """检查是否还能借阅"""
        return self.current_borrow_count < self.MAX_BORROW_LIMIT

    def increment_borrow_count(self):
        self.current_borrow_count += 1

    def decrement_borrow_count(self):
        if self.current_borrow_count > 0:
            self.current_borrow_count -= 1

    def __repr__(self):
        return f"Borrower(id='{self.borrower_id}', name='{self.name}')"


class BorrowRecord:
    """借阅记录模型"""
    def __init__(self, record_id: int, isbn: str, borrower_id: str, borrow_date: date):
        self.record_id = record_id
        self.isbn = isbn
        self.borrower_id = borrower_id
        self.borrow_date = borrow_date
        self.due_date = borrow_date + timedelta(days=14)  # 默认借阅周期14天
        self.return_date: Optional[date] = None  # 实际归还日期，None表示未归还

    def is_returned(self) -> bool:
        return self.return_date is not None

    def return_book(self, return_date: date):
        self.return_date = return_date

    def __repr__(self):
        return f"BorrowRecord(id={self.record_id}, isbn='{self.isbn}', borrower='{self.borrower_id}', returned={self.is_returned()})"