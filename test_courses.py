#!/usr/bin/env python
# coding: utf-8

from fais_mes_courses import MonopBot, InvalidDeliveryDate, Item

from unittest import TestCase
from datetime import datetime, timedelta
from mock import Mock, patch


class MonopBotTest(TestCase):

    @patch('fais_mes_courses.WebDriverWait')
    @patch.object(MonopBot,'get_basket_items', Mock(return_value={'1':"beurre", '2':"lait"}))
    def setUp(self, mockWDW):
        self.bot = MonopBot(Mock(), 'user', 'pass', 1)

    def _setup_picking_slot_mocks(self):
        valid_mock = Mock()
        valid_mock.get_attribute.return_value = "libre"
        invalid_mock = Mock()
        invalid_mock.get_attribute.return_value = "nondispo"

        self.table_cells = {"h3 j1": invalid_mock,
                            "h3 j2": valid_mock,
                            "h5 j3": invalid_mock,
                            "h6 j3": valid_mock,
                            "h8 j3": invalid_mock}

        def finds_element_css(arg):
            if "headers" in arg:
                return self.table_cells[arg.split('"')[1]]
            return Mock()

        self.bot.driver.find_element_by_css_selector = Mock(side_effect=finds_element_css)

    @patch('fais_mes_courses.WebDriverWait')
    def test_picking_delivery_slots(self, mockWDW):
        self._setup_picking_slot_mocks()

        # date should be after day n+1 at noon
        with self.assertRaises(InvalidDeliveryDate):
            self.bot.set_delivery_time((datetime.now() + timedelta(1)).replace(hour=9))

        # date should be before "in 6 days"
        with self.assertRaises(InvalidDeliveryDate):
            self.bot.set_delivery_time(datetime.now() + timedelta(days=6))

        # date should be between 7 and 21
        with self.assertRaises(InvalidDeliveryDate):
            self.bot.set_delivery_time((datetime.now() + timedelta(days=2)).replace(hour=6))
        with self.assertRaises(InvalidDeliveryDate):
            self.bot.set_delivery_time((datetime.now() + timedelta(days=2)).replace(hour=22))

        # A few available and unavailable dates with special attention to the "12h30"
        # slot of monoprix messing things up
        self.bot.set_delivery_time(
            (datetime.now() + timedelta(days=2)).replace(hour=9))
        with self.assertRaises(InvalidDeliveryDate):
            self.bot.set_delivery_time(
                (datetime.now() + timedelta(days=3)).replace(hour=11))
        self.bot.set_delivery_time(
            (datetime.now() + timedelta(days=3)).replace(hour=12))
        with self.assertRaises(InvalidDeliveryDate):
            self.bot.set_delivery_time(
                (datetime.now() + timedelta(days=3)).replace(hour=13))

    def test_emptying_basket(self):
        self.bot.empty_basket()
        self.assertTrue('button[id="1"]' in self.bot.driver.find_element_by_css_selector.call_args_list[-2][0][0])
        self.assertTrue('button[id="2"]' in self.bot.driver.find_element_by_css_selector.call_args_list[-1][0][0])
        self.assertEqual(0, len(self.bot.basket))

    @patch.object(MonopBot, 'get_previous_order_items')
    def test_add_order_to_basket(self, mock_order):
        mock_order.return_value = [Item('Heudeubert - Biscottes', True, '23'),
                                   Item('Printemps - Carottes', False, '-1'),
                                   Item('Danone - Yaourt', True, '32')]
        order_items = self.bot.get_previous_order_items(1)
        self.bot.add_previous_order_to_basket(1)
        # Check that available items that were not in the basket have been added
        # and unavailable ones have been collected
        for item in order_items:
            if item.available:
                self.assertTrue(item.description in self.bot.basket.values())
            else:
                self.assertTrue(item.description in self.bot.unavailable_items)



        
