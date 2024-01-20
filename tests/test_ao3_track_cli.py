import AO3
from ao3_track_cli.main import add_work, update_work

TEST_WORK_ID = "21990778"


def test_add_work():
    add_work(TEST_WORK_ID)


def test_update_work():
    work = AO3.Work(TEST_WORK_ID, load_chapters=False)
    update_work(work)
