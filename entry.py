import datetime


class Entry:
    """An entry object.

    Each entry has an id number, a date, a task name, the minutes spent, and
    any additional notes. The ID number isn't recorded in the CSV, nor
    displayed, but is assigned for ease of editing/removing specific records.
    """
    def __init__(self, en, entry_date, task_name="N/A", mins_spent=0, notes=""):
        self.entry_ID = en
        self.entry_date = entry_date
        self.task_name = task_name.capitalize()
        self.mins_spent = mins_spent
        self.notes = notes
        
    def get_readable_date(self):
        disp_day = self.entry_date[3:5]
        disp_month = self.entry_date[0:2]
        disp_year = self.entry_date[6:8]
        if int(disp_year) > 17:
            disp_year = str(19) + str(disp_year)
        else:
            disp_year = str(20) + str(disp_year)
        return "{}/{}/{}".format(disp_month, disp_day, disp_year)
