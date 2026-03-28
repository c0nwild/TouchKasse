import sqlite3
import tkinter as tk
from abc import abstractmethod
import time
from datetime import datetime
from collections import namedtuple, Counter, OrderedDict

tk_root_base = tk.Tk()
tk_root_base.geometry('{}x{}'.format(1280, 800))
tk_root_base.resizable(width=False, height=False)
tk_root_base.wm_attributes('-fullscreen', 'true')


class DBAccess:

    def __init__(self, db_name):
        self._db_name = db_name
        self._db_conn = sqlite3.connect(self._db_name)
        self._cursor = self._db_conn.cursor()
        self._tr_list_items = None

    def db_get(self, table_name, item_name: str = '', value: str = '*') -> list:
        """
        Get db entries by name of item
        :param table_name: Name of the sqlite table
        :param value: Specific value to query
        :param item_name: Name of the db item to be queried
        :return: List of all db entries belonging to the item
        """
        if item_name != '':
            cmd = "SELECT ({val}) FROM {table_name} WHERE name_short=?".format(
                val=value,
                table_name=table_name
            )
            self._cursor.execute(cmd, (item_name,))
        else:
            cmd = "SELECT {val} FROM {table_name}".format(
                val=value,
                table_name=table_name
            )
            self._cursor.execute(cmd)
        return self._cursor.fetchall()

    def db_update_sold(self, table_name, item_short_name, sold=0):
        """
        Set db entry for sold items.
        :param table_name: Name of the sqlite table
        :param item_short_name: Short name of the db item to be queried
        :param sold: How many sold items
        :return: Nothing
        """
        cmd = "UPDATE {table_name} SET sold=? WHERE name_short=?".format(
            table_name=table_name
        )
        self._db_conn.execute(cmd, (sold, item_short_name))
        self._db_conn.commit()

    def db_update_custom_sum(self, table_name, item_short_name, custom_sum=0):
        """
        Set db entry for custom sum.
        :param table_name: Name of the sqlite table
        :param item_short_name: Short name of the db item to be queried
        :param custom_sum: Custom sum value
        :return: Nothing
        """
        cmd = "UPDATE {table_name} SET price=? WHERE name_short=?".format(
            table_name=table_name
        )
        self._db_conn.execute(cmd, (custom_sum, item_short_name))
        self._db_conn.commit()

    def set_tr_list_items(self, tr_list_items: list):
        """
        From db.fetchall comes list of tuples. This function can process it and stores it
        in string for the db access command to be used.
        :param tr_list_items: List of tuples with short names for db items.
        :return: zip
        """
        item_list = []
        for item in tr_list_items:
            item_list.append(item[0])

        self._tr_list_items = item_list

    def get_tr_list_items(self):
        """
        :return: List of short names for those items that are stored in the transaction db
        """
        return self._tr_list_items

    def db_create_transaction_entry(self, table_name, values: list):
        """
        Create db entry
        :param table_name: Name of the sqlite table
        :param values: List of values to be inserted into db table.
        :return: nothing
        """
        items = 'date, bill, cash, ' + ','.join(self._tr_list_items)
        placeholders = ','.join(['?'] * len(values))
        cmd = 'INSERT INTO {table_name} ({items}) VALUES ({placeholders})'.format(
            table_name=table_name,
            items=items,
            placeholders=placeholders
        )
        self._db_conn.execute(cmd, values)
        self._db_conn.commit()


class UIFrameItem:

    def __init__(self, name, width, height, tk_root, pos='', color='white'):
        """
        Create tkinter frame object
        :param name:
        :param width:
        :param height:
        :param tk_root:
        :param pos:
        :param color:
        """
        self._tk_master = tk_root
        self._name = name
        self._width = width
        self._height = height
        self._pos = pos
        self._color = color
        self._frame = self.make_frame()

    def make_frame(self) -> tk.Frame:
        """
        Generate tkinter frame object
        :return: Tkinter frame object
        """
        return tk.Frame(self._tk_master,
                        width=self._width,
                        height=self._height,
                        bg=self._color)

    def get_frame(self) -> tk.Frame:
        """
        Get reference to frame object
        :return:tkinter frame object
        """
        return self._frame

    def clear(self):
        """
        Recreate frame object
        :return: Nothing
        """
        self._frame.destroy()
        self._frame = self.make_frame()
        self._frame.pack_propagate(False)

        if self._pos != '':
            self._frame.pack(side=self._pos)
        else:
            self._frame.pack()


class UIButtonItem:

    def __init__(self, name, short_name, _tk_root):
        self._tk_master = _tk_root
        self._name = name
        self._short_name = short_name
        self._event_cb = None

    def generate_button(self) -> tk.Button:
        """

        :return:tkinter button object
        """
        return tk.Button(self._tk_master,
                         text=self._name,
                         font=('Arial', 16),
                         width=100,
                         height=2,
                         command=self.button_callback)

    def get_name(self):
        """

        :return:
        """
        return self._name

    @abstractmethod
    def button_callback(self):
        pass


class FoodButtonItem(UIButtonItem):

    def __init__(self, name, short_name, price, _tk_root):
        super(FoodButtonItem, self).__init__(name, short_name, _tk_root)
        self._tk_master = _tk_root
        self._price = price
        self._sold = 0

    def button_callback(self):
        if self._event_cb is not None:
            self._event_cb(self._name, self._short_name, self._price)

    def attach_external_callback(self, cb):
        self._event_cb = cb


class CashButtonItem(UIButtonItem):

    def __init__(self, name, value, _tk_root):
        super(CashButtonItem, self).__init__(name, '', _tk_root)
        self._tk_master = _tk_root
        self._value = value

    def button_callback(self):
        if self._event_cb is not None:
            self._event_cb(self._value)

    def attach_external_callback(self, cb):
        self._event_cb = cb

    def generate_button(self) -> tk.Button:
        """

        :return:tkinter button object
        """
        return tk.Button(self._tk_master,
                         text=self._name,
                         font=('Arial', 20),
                         width=100,
                         height=2,
                         command=self.button_callback)


class CashPad:

    def __init__(self, tk_root_frame: UIFrameItem, tk_value_display: tk.Label = None):
        self._value = 0.0
        self._tk_root_frame = tk_root_frame
        self._tk_value_display = tk_value_display
        self.cash_button_factory()

    def cash_button_factory(self):
        b_elem = []
        cash_values_cent = {
            '1 Cent': 0.01,
            '2 Cent': 0.02,
            '5 Cent': 0.05,
            '10 Cent': 0.1,
            '20 Cent': 0.2,
            '50 Cent': 0.5
        }
        cash_values_euro = {
            '1 €': 1,
            '2 €': 2,
            '5 €': 5,
            '10 €': 10,
            '20 €': 20,
            '50 €': 50,
            '100 €': 100
        }

        tk_cent_button_frame = UIFrameItem('cent buttons',
                                           height=650,
                                           width=320,
                                           tk_root=self._tk_root_frame.get_frame())

        tk_euro_button_frame = UIFrameItem('euro buttons',
                                           height=650,
                                           width=320,
                                           tk_root=self._tk_root_frame.get_frame())

        tk_cent_button_frame.get_frame().pack_propagate(False)
        tk_cent_button_frame.get_frame().pack(side=tk.LEFT)

        tk_euro_button_frame.get_frame().pack_propagate(False)
        tk_euro_button_frame.get_frame().pack(side=tk.LEFT)

        for name, value in cash_values_cent.items():
            obj = CashButtonItem(name, value, tk_cent_button_frame.get_frame())
            obj.attach_external_callback(self.update_value)
            b_elem.append(obj.generate_button())

        for name, value in cash_values_euro.items():
            obj = CashButtonItem(name, value, tk_euro_button_frame.get_frame())
            obj.attach_external_callback(self.update_value)
            b_elem.append(obj.generate_button())

        for b in b_elem:
            b.pack()

    def update_value(self, value):
        self._value += value
        if self._tk_value_display is not None:
            self._tk_value_display.config(
                text="BAR: {cash:.02f} €".format(
                    cash=self._value
                )
            )

    def get_value(self):
        return self._value

    def reset_value(self):
        self._value = 0
        self.update_value(0)


class TouchRegisterUI:
    """Main class for tkinter UI"""

    def __init__(self):
        self.display_elements = []
        self.button_shortnames = []
        self.tr_counter = Counter()
        self.total_cash = 0.0
        self.current_cash = 0.0
        self.current_sum = 0.0
        self.current_custom_sum = 0.0
        self.db_interface = DBAccess('touchReg.db')
        self.transaction_done = False
        self.cash_pad = None

        self.db_elements = self.db_interface.db_get('food_list')

        """Main frame"""
        self.tk_main_frame = UIFrameItem('main_frame',
                                         width=1280,
                                         height=800,
                                         tk_root=tk_root_base)
        self.tk_main_frame.get_frame().pack()

        """Display"""
        self.tk_display_frame = UIFrameItem('display_frame',
                                            width=640,
                                            height=800,
                                            tk_root=self.tk_main_frame.get_frame())
        self.tk_display_frame.get_frame().pack_propagate(False)
        self.tk_display_frame.get_frame().pack(side=tk.LEFT)

        display_scroll_frame = tk.Frame(self.tk_display_frame.get_frame(), width=640, height=700)
        display_scroll_frame.pack_propagate(False)
        display_scroll_frame.pack()

        self._display_scrollbar = tk.Scrollbar(display_scroll_frame, orient=tk.VERTICAL, width=34)
        self._display_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._display_canvas = tk.Canvas(display_scroll_frame,
                                         yscrollcommand=self._display_scrollbar.set,
                                         highlightthickness=0)
        self._display_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._display_scrollbar.config(command=self._display_canvas.yview)

        self._display_inner_frame = tk.Frame(self._display_canvas)
        self._display_canvas.create_window((0, 0), window=self._display_inner_frame, anchor=tk.NW)
        self._display_inner_frame.bind(
            '<Configure>',
            lambda _: self._display_canvas.configure(
                scrollregion=self._display_canvas.bbox('all')
            )
        )

        self.tk_display_sum = tk.Label(self.tk_display_frame.get_frame(),
                                       text='SUMME',
                                       justify=tk.LEFT,
                                       anchor=tk.W,
                                       width=640,
                                       font=('Arial', 20),
                                       pady=10,
                                       padx=10
                                       )
        self.tk_display_sum.pack_propagate(False)
        self.tk_display_sum.pack(side=tk.BOTTOM)

        self.tk_display_cash = tk.Label(self.tk_display_frame.get_frame(),
                                        text='BAR',
                                        justify=tk.LEFT,
                                        anchor=tk.W,
                                        width=640,
                                        font=('Arial', 20),
                                        pady=10,
                                        padx=10
                                        )
        self.tk_display_cash.pack_propagate(False)
        self.tk_display_cash.pack(side=tk.BOTTOM)

        """Frame für Essenstasten und Funktionstasten"""
        self.tk_food_function_frame = tk.Frame(self.tk_main_frame.get_frame(), height=800, width=640)
        self.tk_food_function_frame.pack_propagate(False)
        self.tk_food_function_frame.pack(side=tk.RIGHT)

        """Frame für Essens-/Geldtasten"""
        self.tk_food_frame = UIFrameItem('food_buttons',
                                         width=640,
                                         height=650,
                                         color='red',
                                         tk_root=self.tk_food_function_frame)
        self.tk_food_frame.get_frame().pack_propagate(False)
        self.tk_food_frame.get_frame().pack()
        self.food_buttons = self.food_button_factory()

        """Frame für Funktionstasten"""
        self.tk_function_frame = UIFrameItem('function_buttons',
                                             width=640,
                                             height=150,
                                             color='green',
                                             tk_root=self.tk_food_function_frame)
        self.tk_function_frame.get_frame().pack_propagate(False)
        self.tk_function_frame.get_frame().pack()
        self.food_function_element_factory()

        """prepare db access function for transfer list"""
        tr_list_items = self.db_interface.db_get('food_list', value='name_short')
        self.db_interface.set_tr_list_items(tr_list_items)

    def food_button_factory(self):
        b_elem = []

        col1_frame = tk.Frame(self.tk_food_frame.get_frame(), width=320, height=650)
        col1_frame.pack_propagate(False)
        col1_frame.pack(side=tk.LEFT)

        col2_frame = tk.Frame(self.tk_food_frame.get_frame(), width=320, height=650)
        col2_frame.pack_propagate(False)
        col2_frame.pack(side=tk.LEFT)

        col1_count = 0
        for element in self.db_elements:
            """db entry: id|name|shortname|price|sold """
            name = element[1]
            short_name = element[2]
            price = element[3]
            if name != '':
                parent = col1_frame if col1_count < 10 else col2_frame
                obj = FoodButtonItem(name, short_name, price, parent)
                obj.attach_external_callback(self.display_element_factory)
                obj.generate_button().pack()
                b_elem.append(short_name)
                col1_count += 1

        return b_elem

    def display_element_factory(self, name, short_name, price):
        if self.transaction_done is True:
            self.reset_transaction()

        #self.got_cash_button.config(state='active')

        disp_obj = {
            'tk_name': tk.Label(self._display_inner_frame,
                                text=name,
                                font=('Arial', 15),
                                justify=tk.LEFT,
                                anchor=tk.W,
                                width=250,
                                padx=10
                                ),
            'tk_price': tk.Label(self._display_inner_frame,
                                 text="{price:.02f}€".format(price=price),
                                 font=('Arial', 15),
                                 justify=tk.LEFT,
                                 anchor=tk.W,
                                 width=250,
                                 padx=20
                                 ),
            'name': name,
            'short_name': short_name,
            'price': price
        }
        disp_obj['tk_name'].pack()
        disp_obj['tk_price'].pack()

        self.display_elements.append(disp_obj)
        self._display_inner_frame.update_idletasks()
        self._display_canvas.yview_moveto(1.0)

        self.tr_counter = self.update_sum()

    def food_function_element_factory(self):
        got_cash_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                         width=160,
                                         height=150)
        self.got_cash_button = tk.Button(got_cash_button_frame,
                                         text='Gegeben',
                                         font=('Arial', 20),
                                         width=100,
                                         height=100,
                                         command=self.got_cash)

        cancel_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                       width=160,
                                       height=150)
        cancel_button = tk.Button(cancel_button_frame,
                                  text='Abbrechen',
                                  font=('Arial', 20),
                                  width=100,
                                  height=100,
                                  command=lambda: self.end_transaction('cancel'))

        custom_price_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                             width=160,
                                             height=150)
        self.custom_price_button = tk.Button(custom_price_button_frame,
                                             text='Betrag',
                                             font=('Arial', 20),
                                             width=100,
                                             height=100,
                                             command=self.custom_price)

        summary_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                        width=160,
                                        height=150)
        summary_button = tk.Button(summary_button_frame,
                                   text='Übersicht',
                                   font=('Arial', 20),
                                   width=100,
                                   height=100,
                                   command=self.show_summary)

        got_cash_button_frame.pack_propagate(False)
        got_cash_button_frame.pack(side=tk.LEFT)
        cancel_button_frame.pack_propagate(False)
        cancel_button_frame.pack(side=tk.LEFT)
        custom_price_button_frame.pack_propagate(False)
        custom_price_button_frame.pack(side=tk.LEFT)
        summary_button_frame.pack_propagate(False)
        summary_button_frame.pack(side=tk.LEFT)
        self.got_cash_button.pack()
        self.custom_price_button.pack()
        cancel_button.pack()
        summary_button.pack()

    def got_cash_function_element_factory(self):
        got_cash_ok_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                            width=215,
                                            height=150)
        got_cash_ok_button = tk.Button(got_cash_ok_button_frame,
                                       text='Ok',
                                       font=('Arial', 20),
                                       width=100,
                                       height=100,
                                       command=lambda: self.end_transaction('ok'))

        got_cash_reset_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                               width=215,
                                               height=150)
        got_cash_reset_button = tk.Button(got_cash_reset_button_frame,
                                          text='Löschen',
                                          font=('Arial', 20),
                                          width=100,
                                          height=100,
                                          command=self.cash_pad.reset_value)

        got_cash_cancel_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                                width=210,
                                                height=150)
        got_cash_cancel_button = tk.Button(got_cash_cancel_button_frame,
                                           text='Abbrechen',
                                           font=('Arial', 20),
                                           width=100,
                                           height=100,
                                           command=lambda: self.end_transaction('cancel'))

        got_cash_ok_button_frame.pack_propagate(False)
        got_cash_ok_button_frame.pack(side=tk.LEFT)
        got_cash_reset_button_frame.pack_propagate(False)
        got_cash_reset_button_frame.pack(side=tk.LEFT)
        got_cash_cancel_button_frame.pack_propagate(False)
        got_cash_cancel_button_frame.pack(side=tk.LEFT)
        got_cash_ok_button.pack()
        got_cash_reset_button.pack()
        got_cash_cancel_button.pack()

    def custom_price_function_element_factory(self):
        custom_price_ok_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                                width=215,
                                                height=150)
        custom_price_ok_button = tk.Button(custom_price_ok_button_frame,
                                           text='Ok',
                                           font=('Arial', 20),
                                           width=100,
                                           height=100,
                                           command=lambda: self.end_transaction('custom price')
                                           )

        custom_price_reset_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                                   width=215,
                                                   height=150)
        custom_price_reset_button = tk.Button(custom_price_reset_button_frame,
                                              text='Löschen',
                                              font=('Arial', 20),
                                              width=100,
                                              height=100,
                                              command=self.cash_pad.reset_value)

        custom_price_cancel_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                                    width=210,
                                                    height=150)
        custom_price_cancel_button = tk.Button(custom_price_cancel_button_frame,
                                               text='Abbrechen',
                                               font=('Arial', 20),
                                               width=100,
                                               height=100,
                                               command=lambda: self.end_transaction('cancel'))

        custom_price_ok_button_frame.pack_propagate(False)
        custom_price_ok_button_frame.pack(side=tk.LEFT)
        custom_price_reset_button_frame.pack_propagate(False)
        custom_price_reset_button_frame.pack(side=tk.LEFT)
        custom_price_cancel_button_frame.pack_propagate(False)
        custom_price_cancel_button_frame.pack(side=tk.LEFT)
        custom_price_ok_button.pack()
        custom_price_reset_button.pack()
        custom_price_cancel_button.pack()

    def clear_display_element_list(self):
        for widget in self._display_inner_frame.winfo_children():
            widget.destroy()
        self.display_elements.clear()
        self._display_canvas.yview_moveto(0)
        self.update_sum()

    def got_cash(self):
        self.tk_food_frame.clear()
        self.tk_function_frame.clear()

        self.cash_pad = CashPad(self.tk_food_frame, self.tk_display_cash)

        self.got_cash_function_element_factory()

    def custom_price(self):
        self.tk_food_frame.clear()
        self.tk_function_frame.clear()

        self.cash_pad = CashPad(self.tk_food_frame, self.tk_display_cash)

        self.custom_price_function_element_factory()

    def end_transaction(self, outcome):
        if outcome == 'ok':
            try:
                self.close_transaction()
            except Exception:
                self.tk_display_cash.config(text="Zu wenig erhalten")
                raise Exception
            else:
                self.transaction_done = True
            finally:
                self.tk_food_frame.clear()
                self.tk_function_frame.clear()
                self.food_buttons = self.food_button_factory()  # restore food buttons
                self.food_function_element_factory()  # restore function buttons

        elif outcome == 'custom price':
            self.display_element_factory('Eigener Betrag', 'EB', self.cash_pad.get_value())
            self.tk_food_frame.clear()
            self.tk_function_frame.clear()
            self.food_buttons = self.food_button_factory()  # restore food buttons
            self.food_function_element_factory()  # restore function buttons

        elif outcome == 'cancel':
            self.reset_transaction()

    def close_transaction(self):
        """
        Display return money and check in data in DB.
        :return:
        """
        transaction_log_items = list()
        item_short_names = self.db_interface.get_tr_list_items()
        item_dict = OrderedDict([(i, 0) for i in item_short_names])

        cash_back = self.cash_pad.get_value() - self.current_sum

        if cash_back < 0:
            raise Exception

        self.tk_display_cash.config(
            text="ZURÜCK: {cash:.02f} €".format(
                cash=cash_back
            )
        )

        date = datetime.now()

        transaction_log_items.append(date.ctime())
        transaction_log_items.append(round(self.current_sum, 2))
        transaction_log_items.append(self.cash_pad.get_value())

        for short_name in self.tr_counter:
            sold = self.tr_counter[short_name]
            item_dict[short_name] = sold
            sold_cumul = sold + self.db_interface.db_get('food_list', item_name=short_name, value='sold')[0][0]
            # Update db with new sold value or custom sum for EB... not perfect but works for now
            if short_name == 'EB':
                total_custom_sum = self.db_interface.db_get('food_list', item_name=short_name, value='price')[0][0] + self.current_custom_sum
                self.db_interface.db_update_custom_sum('food_list', item_short_name=short_name, custom_sum=total_custom_sum)
            else:
                self.db_interface.db_update_sold('food_list', item_short_name=short_name, sold=sold_cumul)


        for key in item_dict.keys():
            transaction_log_items.append(item_dict[key])

        print(transaction_log_items)
        self.db_interface.db_create_transaction_entry('tr_list', transaction_log_items)

    def reset_transaction(self):
        self.tk_food_frame.clear()
        self.tk_function_frame.clear()
        self.food_buttons = self.food_button_factory()  # restore food buttons
        self.food_function_element_factory()
        if self.cash_pad is not None:
            self.cash_pad.reset_value()
        self.clear_display_element_list()
        self.update_sum()
        self.transaction_done = False
        # self.got_cash_button.config(state='disabled')

    def show_summary(self):
        if self.cash_pad is not None:
            self.cash_pad.reset_value()
        self.clear_display_element_list()
        self.transaction_done = False

        self.tk_food_frame.clear()
        self.tk_function_frame.clear()

        items = self.db_interface.db_get('food_list')
        frame = self.tk_food_frame.get_frame()

        col_widths = (380, 110, 120)  # Pixel-Breiten: Artikel, Verkauft, Umsatz
        font_normal = ('Arial', 10)
        font_bold = ('Arial', 10, 'bold')

        def make_row(parent, col1, col2, col3, font, bg=None):
            kw = {'bg': bg} if bg else {}
            row = tk.Frame(parent, **kw)
            row.pack(fill=tk.X, padx=10)
            for text, w, anchor in [(col1, col_widths[0], tk.W),
                                     (col2, col_widths[1], tk.E),
                                     (col3, col_widths[2], tk.E)]:
                cell = tk.Frame(row, width=w, height=25, **kw)
                cell.pack_propagate(False)
                cell.pack(side=tk.LEFT)
                tk.Label(cell, text=text, font=font, anchor=anchor, **kw).pack(fill=tk.BOTH, expand=True)

        # Header
        make_row(frame, 'Artikel', 'Verkauft', 'Umsatz', font_bold, bg='lightgray')
        tk.Frame(frame, height=1, bg='gray').pack(fill=tk.X, padx=10)

        total_income = 0.0
        total_expenses = 0.0

        for item in items:
            name = item[1]
            price = item[3]
            sold = item[4]
            if name == '':
                continue

            amount = price * sold
            if price >= 0:
                total_income += amount
            else:
                total_expenses += amount

            total_custom_income = self.db_interface.db_get('food_list', item_name='EB', value='price')[0][0]

            make_row(frame, name, str(sold), '{:.2f}€'.format(amount), font_normal)

        # Separator
        tk.Frame(frame, height=2, bg='black').pack(fill=tk.X, padx=10, pady=5)

        make_row(frame, 'Einnahmen', '', '{:.2f}€'.format(total_income), font_bold)
        make_row(frame, 'Einnahmen (Eigenbetrag)', '', '{:.2f}€'.format(total_custom_income), font_bold)
        make_row(frame, 'Ausgaben (Pfand)', '', '{:.2f}€'.format(total_expenses), font_bold)
        make_row(frame, 'Gesamt', '', '{:.2f}€'.format(total_income + total_expenses + total_custom_income),
                 font_bold, bg='lightyellow')

        # Zurück-Button im Funktionsbereich
        back_frame = tk.Frame(self.tk_function_frame.get_frame(), width=640, height=150)
        back_frame.pack_propagate(False)
        back_frame.pack()
        tk.Button(back_frame, text='Zurück', font=('Arial', 20),
                  width=100, height=100, command=self.summary_back).pack()

    def summary_back(self):
        self.tk_food_frame.clear()
        self.tk_function_frame.clear()
        self.food_buttons = self.food_button_factory()
        self.food_function_element_factory()

    def update_sum(self):
        cnt = Counter()
        _sum = 0.0
        _custom_sum = 0.0
        for e in self.display_elements:
            _sum = _sum + e['price']
            cnt[e['short_name']] += 1
            if e['short_name'] == 'EB':
                _custom_sum = _custom_sum + e['price']
        txt = "SUMME: {sum:.02f}€".format(sum=_sum)
        self.tk_display_sum.config(text=txt)
        self.current_sum = _sum
        self.current_custom_sum = _custom_sum
        return cnt


if __name__ == "__main__":
    TouchRegisterUI()
    tk_root_base.mainloop()
