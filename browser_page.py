from playwright.async_api import Page

import random


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    async def go_to_last_category(self, categories: list):
        for index_category in range(len(categories)):
            locators = []
            if index_category < 3:
                locators.extend(await self.page.locator('div > span', has_text=categories[index_category]).all())
                locators.extend(await self.page.locator('div > p', has_text=categories[index_category]).all())
                locators.extend(await self.page.locator('div > a > strong', has_text=categories[index_category]).all())
            else:
                locators.extend(
                    await self.page.locator('div > a > div > article > p', has_text=categories[index_category]).all())
                locators.extend(await self.page.locator('div > div > a', has_text=categories[index_category]).all())

            if len(locators) > 0:
                for el in locators:
                    if await el.is_visible():
                        await el.click()
                        await self.page.wait_for_timeout(random.randint(1000, 5000))
                        break

    async def fill_search_query(self, filler: str):
        """
        Задача метода отсеять лишние элементы для выбора нужного поля для ввода поискового запроса
        """
        first_step = await self.page.locator('div > div > div > div > div > div > div > div > div > div > label > input').all()

        second_step = []
        for el in first_step:
            if await el.is_visible():
                if await el.is_enabled():
                    second_step.append(el)

        if len(second_step) > 0:
            await second_step[0].fill(filler)
            await self.page.keyboard.press('Enter')

    async def open_modal_with_cities(self):
        elements = await self.page.locator('span > span > span > span > span', has_text='радиус').all()
        if len(elements) > 0:
            for el in elements:
                if await el.is_visible():
                    await el.click()
                    break

    async def get_all_cities_and_press_button(self, sample: set) -> bool:
        cities = await self.page.locator('div > button > div > span').all()

        for city in cities:
            cur_text = await city.text_content()
            cur_list = {el.lower().strip() for el in cur_text.split(',')}
            if len(sample.intersection(cur_list)) >= len(sample):
                await city.click()
                break
        else:
            return False

        await self.page.wait_for_timeout(random.randint(1000, 3000))
        await self.page.locator('button > span > span', has_text='Показать').click()
        await self.page.wait_for_timeout(random.randint(1000, 3000))

        return True
