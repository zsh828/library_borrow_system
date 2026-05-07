from datetime import date
from src.models import Book, Borrower, BorrowRecord


class LibraryManager:
    """图书馆管理系统核心类"""

    def __init__(self):
        self.books: dict[str, Book] = {}  # ISBN -> Book
        self.borrowers: dict[str, Borrower] = {}  # borrower_id -> Borrower
        self.records: list[BorrowRecord] = []  # 所有借阅记录
        self.next_record_id = 1

    def add_book(self, isbn: str, title: str, author: str) -> Book:
        """
        添加图书
        :param isbn: 图书ISBN
        :param title: 书名
        :param author: 作者
        :return: 新增的图书对象
        :raises ValueError: 如果ISBN重复
        """
        if not isinstance(isbn, str) or not isinstance(title, str) or not isinstance(author, str):
            raise ValueError("ISBN, title, and author must be strings")
        
        if isbn in self.books:
            raise ValueError(f"Book with ISBN '{isbn}' already exists")
        
        book = Book(isbn, title, author)
        self.books[isbn] = book
        return book

    def register_borrower(self, borrower_id: str, name: str) -> Borrower:
        """
        注册借阅人（辅助方法，用于测试和初始化）
        :param borrower_id: 借阅人ID
        :param name: 姓名
        :return: 注册的借阅人对象
        :raises ValueError: 如果借阅人ID已存在
        """
        if not isinstance(borrower_id, str) or not isinstance(name, str):
            raise ValueError("borrower_id and name must be strings")
        
        if borrower_id in self.borrowers:
            raise ValueError(f"Borrower with ID '{borrower_id}' already exists")
        
        borrower = Borrower(borrower_id, name)
        self.borrowers[borrower_id] = borrower
        return borrower

    def borrow_book(self, borrower_id: str, isbn: str, borrow_date: date = None) -> BorrowRecord:
        """
        借阅图书
        :param borrower_id: 借阅人ID
        :param isbn: 图书ISBN
        :param borrow_date: 借阅日期，默认为今天
        :return: 生成的借阅记录
        :raises ValueError: 如果借阅人不存在、图书不存在、图书不在馆、达到借阅上限、已借该书未还等
        """
        if borrow_date is None:
            borrow_date = date.today()

        # 1. 检查借阅人是否存在
        if borrower_id not in self.borrowers:
            raise ValueError(f"Borrower with ID '{borrower_id}' does not exist")

        # 2. 检查图书是否存在
        if isbn not in self.books:
            raise ValueError(f"Book with ISBN '{isbn}' does not exist")

        borrower = self.borrowers[borrower_id]
        book = self.books[isbn]

        # 3. 检查图书是否在馆
        if not book.is_available:
            raise ValueError(f"Book with ISBN '{isbn}' is currently not available")

        # 4. 检查借阅人是否已达到上限
        if not borrower.can_borrow():
            raise ValueError(f"Borrower '{borrower_id}' has reached the maximum borrowing limit of {Borrower.MAX_BORROW_LIMIT}")

        # 5. 检查是否已经借阅了该书且未归还
        for record in self.records:
            if (record.borrower_id == borrower_id and 
                record.isbn == isbn and 
                not record.is_returned()):
                raise ValueError(f"Borrower '{borrower_id}' has already borrowed this book '{isbn}' and it is not yet returned")

        # 6. 创建借阅记录
        record = BorrowRecord(
            record_id=self.next_record_id,
            isbn=isbn,
            borrower_id=borrower_id,
            borrow_date=borrow_date
        )
        self.next_record_id += 1
        self.records.append(record)

        # 7. 更新状态
        book.is_available = False
        borrower.increment_borrow_count()

        return record

    def return_book(self, borrower_id: str, isbn: str, return_date: date = None) -> BorrowRecord:
        """
        归还图书
        :param borrower_id: 借阅人ID
        :param isbn: 图书ISBN
        :param return_date: 归还日期，默认为今天
        :return: 更新的借阅记录
        :raises ValueError: 如果找不到对应的未归还记录
        """
        if return_date is None:
            return_date = date.today()

        # 查找对应的未归还记录
        target_record = None
        for record in self.records:
            if (record.borrower_id == borrower_id and 
                record.isbn == isbn and 
                not record.is_returned()):
                target_record = record
                break

        if target_record is None:
            raise ValueError(f"No active borrowing record found for borrower '{borrower_id}' and book '{isbn}'")

        # 更新记录
        target_record.return_book(return_date)

        # 更新图书状态
        self.books[isbn].is_available = True

        # 更新借阅人状态
        self.borrowers[borrower_id].decrement_borrow_count()

        return target_record

    def get_borrow_history_by_book(self, isbn: str) -> list[BorrowRecord]:
        """
        查询某本书的所有借阅历史
        :param isbn: 图书ISBN
        :return: 按借阅日期降序排列的借阅记录列表
        :raises ValueError: 如果图书不存在
        """
        if isbn not in self.books:
            raise ValueError(f"Book with ISBN '{isbn}' does not exist")

        # 过滤出该书的记录
        book_records = [r for r in self.records if r.isbn == isbn]
        
        # 按借阅日期降序排序
        sorted_records = sorted(book_records, key=lambda r: r.borrow_date, reverse=True)
        
        return sorted_records

    def get_active_borrows_by_borrower(self, borrower_id: str) -> list[BorrowRecord]:
        """
        查询个人未归还的借阅记录
        :param borrower_id: 借阅人ID
        :return: 该人所有未归还的借阅记录
        :raises ValueError: 如果借阅人不存在
        """
        if borrower_id not in self.borrowers:
            raise ValueError(f"Borrower with ID '{borrower_id}' does not exist")

        # 过滤出该借阅人的未归还记录
        active_records = [r for r in self.records if r.borrower_id == borrower_id and not r.is_returned()]
        
        return active_records

    def get_top_borrowed_books(self, n: int = 10) -> list[tuple[Book, int]]:
        """
        获取借阅次数最多的前N本书
        :param n: 返回数量，默认为10
        :return: 元组列表 [(Book, count), ...]，按借阅次数降序，次数相同按ISBN升序
        :raises ValueError: 如果n <= 0
        """
        if n <= 0:
            raise ValueError("Number of books to return must be positive")

        # 统计每本书的借阅次数（只统计成功借阅的记录，无论是否归还）
        borrow_counts: dict[str, int] = {}
        for record in self.records:
            isbn = record.isbn
            borrow_counts[isbn] = borrow_counts.get(isbn, 0) + 1

        # 转换为 (Book, count) 格式
        result = []
        for isbn, count in borrow_counts.items():
            if isbn in self.books:
                result.append((self.books[isbn], count))

        # 排序：先按次数降序，再按ISBN升序
        result.sort(key=lambda x: (-x[1], x[0].isbn))

        return result[:n]