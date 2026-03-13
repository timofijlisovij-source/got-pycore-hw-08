import pickle
import re
from collections import UserDict
from datetime import datetime, timedelta
from typing import Optional

# Константи
FILENAME = "addressbook.pkl"
DATE_FORMAT = "%d.%m.%Y"


def save_data(book, filename=FILENAME):
    """Зберігає адресну книгу у файл."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename=FILENAME):
    """Завантажує адресну книгу або створює нову, якщо файл відсутній."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError):
        return AddressBook()


def input_error(func):
    """Декоратор для обробки типових помилок введення."""
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Give me name and value please."
    return inner


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """Клас для імені контакту. Обов'язкове поле."""
    pass


class Phone(Field):
    """Клас для телефону з валідацією формату."""
    def __init__(self, value):
        # Очищуємо номер від дужок, тире та пробілів
        clean_phone = re.sub(r"\D", "", value)
        if len(clean_phone) != 10:
            raise ValueError("Phone must contain 10 digits.")
        super().__init__(clean_phone)


class Birthday(Field):
    """Клас для дня народження з перевіркою формату дати."""
    def __init__(self, value):
        try:
            date_obj = datetime.strptime(value, DATE_FORMAT).date()
            super().__init__(date_obj)
        except ValueError:
            raise ValueError(f"Invalid date format. Use {DATE_FORMAT}")


class Record:
    """Клас для зберігання інформації про контакт."""
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        # Видаляємо номер, порівнюючи очищені значення
        clean_phone = re.sub(r"\D", "", phone)
        for p in self.phones:
            if p.value == clean_phone:
                self.phones.remove(p)
                return
        raise ValueError("Phone not found.")

    def edit_phone(self, old_phone, new_phone):
        self.remove_phone(old_phone)
        self.add_phone(new_phone)

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        bday = self.birthday.value.strftime(DATE_FORMAT) if self.birthday else "N/A"
        return f"Contact: {self.name.value}, phones: {phones}, birthday: {bday}"


class AddressBook(UserDict):
    """Клас-контейнер для всіх записів."""
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name) -> Optional[Record]:
        return self.data.get(name)

    def get_upcoming_birthdays(self):
        """Повертає список привітань на найближчі 7 днів."""
        today = datetime.today().date()
        upcoming = []

        for record in self.data.values():
            if not record.birthday:
                continue

            bday = record.birthday.value.replace(year=today.year)
            if bday < today:
                bday = bday.replace(year=today.year + 1)

            if 0 <= (bday - today).days <= 7:
                # Переносимо вихідні на понеділок
                congrat_date = bday
                if congrat_date.weekday() >= 5:
                    congrat_date += timedelta(days=(7 - congrat_date.weekday()))
                
                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": congrat_date.strftime(DATE_FORMAT)
                })
        return upcoming


# --- Обробники команд ---

@input_error
def add_contact(args, book):
    name, phone = args
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return "Contact updated."


@input_error
def change_contact(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Phone changed."
    raise KeyError


@input_error
def add_birthday(args, book):
    name, bday = args
    record = book.find(name)
    if record:
        record.add_birthday(bday)
        return "Birthday added."
    raise KeyError


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ").strip()
        if not user_input:
            continue
            
        command, *args = user_input.split()
        command = command.lower()

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            record = book.find(args[0])
            print(record if record else "Not found.")
        elif command == "all":
            for record in book.data.values():
                print(record)
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "birthdays":
            upcoming = book.get_upcoming_birthdays()
            for entry in upcoming:
                print(f"{entry['name']}: {entry['congratulation_date']}")
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
