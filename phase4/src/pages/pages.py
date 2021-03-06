from time import sleep

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .page_elements import Element, CreateEditIssueDialog, InputElement, IssueDetails, IssueListItem


class BasePage(object):
    def __init__(self, driver):
        self.driver = driver

    def go(self, url):
        self.driver.get(url)

    def is_title_contains(self, title):
        return title in self.driver.title


class GeneralPage(BasePage):
    create_issue_link = (By.XPATH, "//*[@id='create_link']")
    issues_menu_link = (By.XPATH, "//*[@id='find_link']")
    issues_menu_dropdown = (By.XPATH, "//*[@id='find_link-content']")
    issues_menu_item_search = (By.XPATH, "//a[text()='Search for issues']")
    create_issue_dialog_locator = (By.XPATH, "//*[@id='create-issue-dialog']")

    aui_message_container_locator = (By.XPATH, "//*[@id='aui-flag-container']")
    aui_message_issue_link_locator = (By.XPATH, "//*[@id='aui-flag-container']//a")

    def __init__(self, driver):
        BasePage.__init__(self, driver)

        self.create_issue_link = Element(self.driver, GeneralPage.create_issue_link)
        self.issues_link = Element(self.driver, GeneralPage.issues_menu_link)
        self.issues_dropdown_menu = Element(self.driver, GeneralPage.issues_menu_dropdown)
        self.issues_menu_item_search = Element(self.driver, GeneralPage.issues_menu_item_search)
        self.create_issue_dialog = CreateEditIssueDialog(self.driver, GeneralPage.create_issue_dialog_locator)
        self.aui_message_container = Element(self.driver, GeneralPage.aui_message_container_locator)

    def create_issue(self, project, summary, type="Bug", description="", priority="Low"):
        self.create_issue_link.click()
        self.create_issue_dialog.wait_to_be_displayed()

        self.create_issue_dialog.project = project
        self.create_issue_dialog.issue_type = type
        self.create_issue_dialog.summary = summary
        self.create_issue_dialog.description = description
        self.create_issue_dialog.priority = priority
        self.create_issue_dialog.submit()

        if self.aui_message_is_displayed:
            e = Element(self.driver, GeneralPage.aui_message_issue_link_locator)
            return e.text[:e.text.index(' ')]
        else:
            return None

    @property
    def aui_message_is_displayed(self):
        try:
            e = self.aui_message_container.wait_to_be_displayed(10)
            return e.is_displayed
        except TimeoutException:
            return False

    def go_to_search_page(self):
        self.issues_link.click()
        self.issues_dropdown_menu.wait_to_be_displayed(3)
        self.issues_menu_item_search.click()


class DashboardPage(GeneralPage):
    pass


class IssuesSearchPage(GeneralPage):
    advanced_search = (By.XPATH, "//*[@id='advanced-search']")
    issue_list_locator = (By.XPATH, "//ol[contains(@class, 'issue-list')]")
    issue_content_locator = (By.XPATH, "//*[@id='issue-content']")
    edit_issue_dialog_locator = (By.XPATH, "//*[@id='edit-issue-dialog']")

    loading_locator = (By.XPATH, "//div[@class='loading']")

    def __init__(self, driver):
        GeneralPage.__init__(self, driver)

        self.search_field = InputElement(self.driver, IssuesSearchPage.advanced_search)
        self.issue_list = Element(self.driver, IssuesSearchPage.issue_list_locator)
        self.issue_details = IssueDetails(self.driver, IssuesSearchPage.issue_content_locator)
        self.edit_issue_dialog = CreateEditIssueDialog(self.driver, IssuesSearchPage.edit_issue_dialog_locator)

        self.loading_indicator = Element(self.driver, IssuesSearchPage.loading_locator)

    def wait_for_loading(self, timeout=60):
        self.loading_indicator.wait_to_be_hidden(timeout)
        sleep(5)

    def search(self, jql):
        self.search_field.value = jql
        self.search_field.send_keys(Keys.RETURN)

        self.wait_for_loading()

    def update(self, summary=None, type=None, priority=None, description=None):
        self.issue_details.open_edit()
        self.edit_issue_dialog.wait_to_be_displayed()

        if summary:
            self.edit_issue_dialog.summary = summary
        if type:
            self.edit_issue_dialog.issue_type = type
        if priority:
            self.edit_issue_dialog.priority = priority
        if description:
            self.edit_issue_dialog.description = description

        self.edit_issue_dialog.submit()
        self.aui_message_container.wait_to_be_displayed(10)
        sleep(5)

    @property
    def found_issues(self):
        l = []

        try:
            # if list is displayed, collect items and return the list
            if self.issue_list.is_displayed:
                # find all list items
                items = self.issue_list.find_elements((By.TAG_NAME, "li"))
                for item in items:
                    l.append(IssueListItem(self.driver, item))
        except TimeoutException:
            # list is not displayed, no items
            pass

        return l


class LoginPage(BasePage):
    login_form_username = (By.XPATH, "//input[@id='login-form-username']")
    login_form_password = (By.XPATH, "//input[@id='login-form-password']")
    login_form_login_btn = (By.XPATH, "//*[@id='login']")
    login_form_error_message = (By.XPATH, "//div[@id='usernameerror']/p")

    details_user_fullname = (By.XPATH, "//a[@id='header-details-user-fullname']")

    def __init__(self, driver):
        BasePage.__init__(self, driver)

        self.login_text = InputElement(self.driver, LoginPage.login_form_username)
        self.password_text = InputElement(self.driver, LoginPage.login_form_password)
        self.login_btn = InputElement(self.driver, LoginPage.login_form_login_btn)

    def login(self, username, password):
        self.login_text.value = username
        self.password_text.value = password

        self.login_btn.click()

    @property
    def is_logged_in(self):
        try:
            details_user_fullname = WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located(LoginPage.details_user_fullname))

            return details_user_fullname.is_displayed()
        except TimeoutException:
            return False

    @property
    def login_error_message(self):
        try:
            w = WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located(LoginPage.login_form_error_message))

            return w.text
        except TimeoutException:
            return ""