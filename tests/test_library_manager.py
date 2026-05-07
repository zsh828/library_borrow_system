import pytest
from datetime import date, timedelta
from src.library_manager import LibraryManager
from src.models import Book, Borrower, BorrowRecord


@pytest.fixture
def library():
    """创建一个空的图书馆管理器实例"""
    return LibraryManager()


@pytest.fixture
def sample_data(library):
    """准备一些示例数据"""
    # 添加图书
    book1 = library.add_book("978-0-13-468599-1", "The C Programming Language", "Kernighan & Ritchie")
    book2 = library.add_book("978-0-596-51774-8", "JavaScript: The Good Parts", "Douglas Crockford")
    book3 = library.add_book("978-0-13-235088-4", "Clean Code", "Robert C. Martin")

    # 注册借阅人
    borrower1 = library.register_borrower("B001", "Alice")
    borrower2 = library.register_borrower("B002", "Bob")

    return {"library": library, "book1": book1, "book2": book2, "book3": book3, 
            "borrower1": borrower1, "borrower2": borrower2}


# --- 测试添加图书 ---

class TestAddBook:
    def test_add_new_book_success(self, library):
        book = library.add_book("123", "Test Book", "Author")
        assert book.isbn == "123"
        assert book.title == "Test Book"
        assert book.author == "Author"
        assert book.is_available is True
        assert len(library.books) == 1

    def test_add_duplicate_isbn_raises_error(self, library):
        library.add_book("123", "Book One", "Author A")
        with pytest.raises(ValueError, match="already exists"):
            library.add_book("123", "Book Two", "Author B")

    def test_add_book_with_invalid_types_raises_error(self, library):
        with pytest.raises(ValueError, match="must be strings"):
            library.add_book(123, "Book", "Author")
        with pytest.raises(ValueError, match="must be strings"):
            library.add_book("123", 123, "Author")
        with pytest.raises(ValueError, match="must be strings"):
            library.add_book("123", "Book", 123)


# --- 测试注册借阅人 ---

class TestRegisterBorrower:
    def test_register_new_borrower_success(self, library):
        borrower = library.register_borrower("B001", "Alice")
        assert borrower.borrower_id == "B001"
        assert borrower.name == "Alice"
        assert borrower.current_borrow_count == 0
        assert len(library.borrowers) == 1

    def test_register_duplicate_borrower_raises_error(self, library):
        library.register_borrower("B001", "Alice")
        with pytest.raises(ValueError, match="already exists"):
            library.register_borrower("B001", "Alice Duplicate")

    def test_register_borrower_with_invalid_types_raises_error(self, library):
        with pytest.raises(ValueError, match="must be strings"):
            library.register_borrower(123, "Alice")
        with pytest.raises(ValueError, match="must be strings"):
            library.register_borrower("B001", 123)


# --- 测试借阅图书 ---

class TestBorrowBook:
    def test_borrow_book_success(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        isbn = sample_data["book1"].isbn
        today = date.today()

        record = lib.borrow_book(b_id, isbn, today)

        assert record.borrower_id == b_id
        assert record.isbn == isbn
        assert record.borrow_date == today
        assert record.is_returned() is False
        
        # 检查状态更新
        assert sample_data["book1"].is_available is False
        assert sample_data["borrower1"].current_borrow_count == 1

    def test_borrow_nonexistent_borrower_raises_error(self, sample_data):
        lib = sample_data["library"]
        with pytest.raises(ValueError, match="does not exist"):
            lib.borrow_book("NONEXISTENT", sample_data["book1"].isbn)

    def test_borrow_nonexistent_book_raises_error(self, sample_data):
        lib = sample_data["library"]
        with pytest.raises(ValueError, match="does not exist"):
            lib.borrow_book(sample_data["borrower1"].borrower_id, "NONEXISTENT_ISBN")

    def test_borrow_unavailable_book_raises_error(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        isbn = sample_data["book1"].isbn
        
        # 先借走
        lib.borrow_book(b_id, isbn)
        
        # 另一个借阅人尝试借同一本（此时书不可用）
        with pytest.raises(ValueError, match="not available"):
            lib.borrow_book(sample_data["borrower2"].borrower_id, isbn)

    def test_borrow_already_borrowed_book_raises_error(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        isbn = sample_data["book1"].isbn
        
        # 先借走
        lib.borrow_book(b_id, isbn)
        
        # 再次尝试借阅同一本未还的书，应触发“已借未还”错误
        with pytest.raises(ValueError, match="already borrowed"):
            lib.borrow_book(b_id, isbn)

    def test_borrow_reaches_limit_raises_error(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        
        # 借满5本
        for i in range(5):
            isbn = f"LIMIT_TEST_{i}"
            lib.add_book(isbn, f"Book {i}", "Author")
            lib.borrow_book(b_id, isbn)
        
        # 第6本应该失败
        new_isbn = "LIMIT_EXCEED_6"
        lib.add_book(new_isbn, "Book Exceed", "Author")
        with pytest.raises(ValueError, match="maximum borrowing limit"):
            lib.borrow_book(b_id, new_isbn)

    def test_borrow_same_book_twice_unreturned_raises_error(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        isbn = sample_data["book1"].isbn
        
        # 第一次借阅
        lib.borrow_book(b_id, isbn)
        
        # 第二次尝试借阅同一本未还的书
        with pytest.raises(ValueError, match="already borrowed"):
            lib.borrow_book(b_id, isbn)


# --- 测试归还图书 ---

class TestReturnBook:
    def test_return_book_success(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        isbn = sample_data["book1"].isbn
        borrow_date = date.today() - timedelta(days=5)
        return_date = date.today()

        # 先借阅
        lib.borrow_book(b_id, isbn, borrow_date)
        
        # 归还
        record = lib.return_book(b_id, isbn, return_date)

        assert record.is_returned() is True
        assert record.return_date == return_date
        
        # 检查状态更新
        assert sample_data["book1"].is_available is True
        assert sample_data["borrower1"].current_borrow_count == 0

    def test_return_nonexistent_record_raises_error(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        isbn = sample_data["book1"].isbn
        
        # 没有借阅过，直接归还
        with pytest.raises(ValueError, match="No active borrowing record"):
            lib.return_book(b_id, isbn)

    def test_return_already_returned_book_raises_error(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        isbn = sample_data["book1"].isbn
        borrow_date = date.today() - timedelta(days=5)
        return_date = date.today()

        # 先借阅并归还
        lib.borrow_book(b_id, isbn, borrow_date)
        lib.return_book(b_id, isbn, return_date)
        
        # 再次归还
        with pytest.raises(ValueError, match="No active borrowing record"):
            lib.return_book(b_id, isbn)


# --- 测试查询借阅历史 ---

class TestGetBorrowHistoryByBook:
    def test_get_history_empty(self, sample_data):
        lib = sample_data["library"]
        isbn = sample_data["book1"].isbn
        
        history = lib.get_borrow_history_by_book(isbn)
        assert history == []

    def test_get_history_sorted_descending(self, sample_data):
        lib = sample_data["library"]
        isbn = sample_data["book1"].isbn
        b_id = sample_data["borrower1"].borrower_id
        
        d1 = date(2023, 1, 1)
        d2 = date(2023, 1, 10)
        d3 = date(2023, 1, 5)
        
        # 多次借阅同一本书
        lib.borrow_book(b_id, isbn, d1)
        lib.return_book(b_id, isbn, d1 + timedelta(days=1))
        
        lib.borrow_book(b_id, isbn, d2)
        lib.return_book(b_id, isbn, d2 + timedelta(days=1))
        
        lib.borrow_book(b_id, isbn, d3)
        lib.return_book(b_id, isbn, d3 + timedelta(days=1))
        
        history = lib.get_borrow_history_by_book(isbn)
        
        # 验证顺序：d2, d3, d1
        assert len(history) == 3
        assert history[0].borrow_date == d2
        assert history[1].borrow_date == d3
        assert history[2].borrow_date == d1

    def test_get_history_for_nonexistent_book_raises_error(self, sample_data):
        lib = sample_data["library"]
        with pytest.raises(ValueError, match="does not exist"):
            lib.get_borrow_history_by_book("NONEXISTENT")


# --- 测试查询个人借阅 ---

class TestGetActiveBorrowsByBorrower:
    def test_get_active_borrows_empty(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        
        active = lib.get_active_borrows_by_borrower(b_id)
        assert active == []

    def test_get_active_borrows_only_unreturned(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        isbn1 = sample_data["book1"].isbn
        isbn2 = sample_data["book2"].isbn
        
        d1 = date.today() - timedelta(days=10)
        d2 = date.today() - timedelta(days=5)
        
        # 借第一本并归还
        lib.borrow_book(b_id, isbn1, d1)
        lib.return_book(b_id, isbn1, d1 + timedelta(days=1))
        
        # 借第二本未还
        lib.borrow_book(b_id, isbn2, d2)
        
        active = lib.get_active_borrows_by_borrower(b_id)
        
        assert len(active) == 1
        assert active[0].isbn == isbn2

    def test_get_active_borrows_for_nonexistent_borrower_raises_error(self, sample_data):
        lib = sample_data["library"]
        with pytest.raises(ValueError, match="does not exist"):
            lib.get_active_borrows_by_borrower("NONEXISTENT")


# --- 测试图书统计 ---

class TestGetTopBorrowedBooks:
    def test_get_top_books_empty(self, sample_data):
        lib = sample_data["library"]
        top = lib.get_top_borrowed_books(10)
        assert top == []

    def test_get_top_books_sorted_by_count_then_isbn(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        
        # 假设我们有几本书
        isbn_a = "A_ISBN"
        isbn_b = "B_ISBN"
        isbn_c = "C_ISBN"
        
        lib.add_book(isbn_a, "Book A", "Auth A")
        lib.add_book(isbn_b, "Book B", "Auth B")
        lib.add_book(isbn_c, "Book C", "Auth C")
        
        # Book A 借了2次
        lib.borrow_book(b_id, isbn_a)
        lib.return_book(b_id, isbn_a)
        lib.borrow_book(b_id, isbn_a)
        lib.return_book(b_id, isbn_a)
        
        # Book B 借了2次
        lib.borrow_book(b_id, isbn_b)
        lib.return_book(b_id, isbn_b)
        lib.borrow_book(b_id, isbn_b)
        lib.return_book(b_id, isbn_b)
        
        # Book C 借了1次
        lib.borrow_book(b_id, isbn_c)
        lib.return_book(b_id, isbn_c)
        
        top = lib.get_top_borrowed_books(10)
        
        # 应该按次数降序，次数相同按ISBN升序
        # A和B都是2次，A < B (字母顺序)，所以 A 在前
        assert len(top) == 3
        assert top[0][0].isbn == isbn_a
        assert top[0][1] == 2
        assert top[1][0].isbn == isbn_b
        assert top[1][1] == 2
        assert top[2][0].isbn == isbn_c
        assert top[2][1] == 1

    def test_get_top_books_limit_n(self, sample_data):
        lib = sample_data["library"]
        b_id = sample_data["borrower1"].borrower_id
        
        # 创建3本书，各借1次
        for i in range(3):
            isbn = f"LIM_{i}"
            lib.add_book(isbn, f"Book {i}", "Auth")
            lib.borrow_book(b_id, isbn)
            lib.return_book(b_id, isbn)
            
        top = lib.get_top_borrowed_books(2)
        
        assert len(top) == 2
        # 由于ISBN是 LIM_0, LIM_1, LIM_2，升序排列
        assert top[0][0].isbn == "LIM_0"
        assert top[1][0].isbn == "LIM_1"

    def test_get_top_books_invalid_n_raises_error(self, sample_data):
        lib = sample_data["library"]
        with pytest.raises(ValueError, match="must be positive"):
            lib.get_top_borrowed_books(0)
        with pytest.raises(ValueError, match="must be positive"):
            lib.get_top_borrowed_books(-1)