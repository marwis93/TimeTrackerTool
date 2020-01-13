from tkinter import messagebox
from jira import JIRA
import datetime

SERVER_ADDRESS = 'http://jiraprod1.delphiauto.net:8080/'
PROJECT_KEY = 'BHE'

EXPECTED_HOURS = 7
EXPECTED_MINUTES = 40
TT_VERSION = "TT_0_4"


def date_convert(s_date):
    """Return the string.

    >>> date_convert('2019-11-28T07:47:21.000+0100')
    '07:47'

    >>> date_convert('2019-11-28T00:00:21.000+0100')
    '00:00'

    >>> date_convert('2019-11-28T12:00:21.000+0100')
    '12:00'

    >>> date_convert('2018-12-28T20:59:59.000+1100')
    '20:59'
    """
    date = datetime.datetime.strptime(s_date, '%Y-%m-%dT%H:%M:%S.000%z')
    return '%02d:%02d' % (date.hour, date.minute)


def calculate_duration(s_date_start, s_date_end):
    """
    Return timedelta object from two strings.

    >>> calculate_duration('2019-11-28T12:00:21.000+0100', '2019-11-28T21:00:21.000+0100')
    datetime.timedelta(seconds=32400)

    >>> calculate_duration('2019-11-28T21:25:21.000+0100', '2019-11-28T21:09:21.000+0100')
    datetime.timedelta(0)
    """
    s_date_start = datetime.datetime.strptime(s_date_start, '%Y-%m-%dT%H:%M:%S.000%z').replace(tzinfo=None)
    if s_date_end is None:
        s_date_end = datetime.datetime.now()
    else:
        s_date_end = datetime.datetime.strptime(s_date_end, '%Y-%m-%dT%H:%M:%S.000%z').replace(tzinfo=None)
    if s_date_end > s_date_start:
        return s_date_end - s_date_start
    else:
        return datetime.timedelta()


def timedelta_to_str(timedelta):
    """
    Return string from timedelta object.

    >>> timedelta_to_str(datetime.timedelta(0))
    '00:00:00'

    >>> timedelta_to_str(datetime.timedelta(days=1))
    '24:00:00'

    >>> timedelta_to_str(datetime.timedelta(seconds=27030))
    '07:30:30'

    >>> timedelta_to_str(datetime.timedelta(days=2, seconds=23430))
    '54:30:30'
    """
    days = timedelta.days
    hours, remainder = divmod(timedelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return '%02d:%02d:%02d' % (hours + (24 * days), minutes, seconds)


class JiraOperations:
    def __init__(self, credentials):
        self.epics_dict = {}
        self.options = {"server": SERVER_ADDRESS}
        self.jira = JIRA(self.options, basic_auth=credentials)
        self.get_epics()

    def get_epics(self):
        found_issues = self.jira.search_issues('project=10031275_mPAD_ITV and type = Epic and summary ~ "Timesheet "')
        for issue in found_issues:
            self.epics_dict[issue.fields.summary] = issue.id

    def get_epic_id(self):
        today = datetime.datetime.now()
        month_name = today.strftime("%B")[:3]
        year = str(today.year)[2:]
        timesheet_string = 'Timesheet ' + month_name + year
        return self.epics_dict[timesheet_string]

    def find_issue_key(self, summary):
        found_issues = self.jira.search_issues('project=10031275_mPAD_ITV and type = Story and reporter = '
                                               'currentUser() and status != done')
        for issue in found_issues:
            if issue.fields.summary.upper().strip() == summary:
                return issue

    def is_story_created(self, summary):
        found_issues = self.jira.search_issues('project=10031275_mPAD_ITV and type = Story and reporter = '
                                               'currentUser() and status != done')
        for issue in found_issues:
            if issue.fields.summary.upper().strip() == summary:
                return True
        return False

    def get_stories_created_today(self):
        issue_list = []
        work_time = datetime.timedelta()
        break_time = datetime.timedelta()
        found_issues = self.jira.search_issues('project=10031275_mPAD_ITV and type = Story and reporter = '
                                               'currentUser() and createdDate > startOfDay() and (status = open OR '
                                               'status = Done)')
        for issue in found_issues:
            issue_list.append("Key: %s, status: %s, summary: %s, created: %s, duration: %s, description: %s"
                              % (issue.key, issue.fields.status, issue.fields.summary,
                                 date_convert(issue.fields.created),
                                 timedelta_to_str(
                                     calculate_duration(issue.fields.created, issue.fields.resolutiondate)),
                                 issue.fields.description))
            if issue.fields.summary.upper().strip() == 'WORK':
                work_time = work_time + calculate_duration(issue.fields.created, issue.fields.resolutiondate)
            elif issue.fields.summary.upper().strip() == 'BREAK':
                break_time = break_time + calculate_duration(issue.fields.created, issue.fields.resolutiondate)

        total_work_today = work_time - break_time
        issue_list.append("Total work time today: %s" % timedelta_to_str(total_work_today))
        return issue_list

    def create_ticket(self, summary, description=''):
        created_issue = self.jira.create_issue(project=PROJECT_KEY,
                                               summary=summary,
                                               description=description,
                                               issuetype={'name': 'Story'},
                                               labels=[TT_VERSION])
        self.jira.add_issues_to_epic(self.get_epic_id(), [created_issue.key])
        return created_issue.key

    def close_ticket(self, ticket_number):
        self.jira.transition_issue(ticket_number, 'done', fields={'resolution': {'name': 'Done'}})

    def description_init(self, summary):
        if self.is_story_created(summary):
            issue = self.find_issue_key(summary)
            if issue.fields.description is not None:
                return issue.fields.description
            else:
                return ''
        else:
            return ''

    def update_description(self, summary, description):
        if self.is_story_created(summary):
            issue_to_update = self.find_issue_key(summary)
            issue_to_update.update(fields={'description': description})
            return True
        else:
            return False

    def get_week_statistics(self):
        week_statistics = []
        work_story = 0
        break_story = 0
        work_time = datetime.timedelta()
        break_time = datetime.timedelta()
        balance = datetime.timedelta()
        work_expected = datetime.timedelta(hours=EXPECTED_HOURS, minutes=EXPECTED_MINUTES)
        found_issues = self.jira.search_issues('project=10031275_mPAD_ITV and type = Story and reporter = '
                                               'currentUser() and createdDate > startOfWeek() and (status = open OR '
                                               'status = Done)')
        for issue in found_issues:
            issue_summary = issue.fields.summary.upper().strip()
            if issue_summary == 'WORK':
                work_time = work_time + calculate_duration(issue.fields.created, issue.fields.resolutiondate)
                work_story += 1
            elif issue_summary == 'BREAK':
                break_time = break_time + calculate_duration(issue.fields.created, issue.fields.resolutiondate)
                break_story += 1
            elif issue_summary.split()[0] == 'BAL':
                hours = int(issue_summary.split()[3])
                minutes = int(issue_summary.split()[5])
                if issue_summary.split()[2] == '+':
                    balance = balance + datetime.timedelta(hours=hours, minutes=minutes)
                    work_time = work_time + datetime.timedelta(hours=hours, minutes=minutes)
                elif issue_summary.split()[2] == '-':
                    balance = balance + datetime.timedelta(hours=hours, minutes=minutes)
                    work_time = work_time - datetime.timedelta(hours=hours, minutes=minutes)
                else:
                    messagebox.showinfo("Error", "Found story with unknown sign: %s." % issue_summary.split()[2])
            else:
                messagebox.showinfo("Error", "Found story with unknown summary: %s." % issue.fields.summary)
        total_work_week = work_time - break_time
        total_work_expected = work_story * work_expected
        if total_work_expected - total_work_week >= datetime.timedelta():
            time_left_today = timedelta_to_str(total_work_expected - total_work_week)
        else:
            time_left_today = '-' + timedelta_to_str(total_work_week - total_work_expected)
        week_statistics.append(
            "Total work stories created this week: %d, total break stories created this week: %d." % (
                work_story, break_story))
        week_statistics.append("Total work time expected this week: %s" % timedelta_to_str(total_work_expected))
        week_statistics.append("Total worked time this week: %s, including %s from balance stories" % (
            timedelta_to_str(total_work_week), str(balance)))
        week_statistics.append("Left time for today: %s" % time_left_today)
        return week_statistics

    def start_work(self):
        if not self.is_story_created('WORK'):
            self.create_ticket('WORK')
            return True
        else:
            return False

    def stop_work(self):
        if self.is_story_created('WORK'):
            issue_key = self.find_issue_key('WORK')
            self.close_ticket(issue_key)
            return True
        else:
            return False

    def start_break(self, description):
        if not self.is_story_created('BREAK'):
            self.create_ticket('BREAK', description)
            return True
        else:
            return False

    def stop_break(self):
        if self.is_story_created('BREAK'):
            issue_key = self.find_issue_key('BREAK')
            self.close_ticket(issue_key)
            return True
        else:
            return False


if __name__ == "__main__":
    import doctest

    doctest.testmod()
