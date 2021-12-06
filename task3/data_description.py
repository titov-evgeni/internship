"""Description of post and user arguments
required to write to the database"""


class PostDataDB:
    """Description of post arguments required to write to the database"""
    __slots__ = ("id",
                 "post_url",
                 "post_date",
                 "number_of_comments",
                 "number_of_votes",
                 "post_category"
                 )


class UserDataDB:
    """Description of user arguments required to write to the database"""
    __slots__ = ("user_name",
                 "user_karma",
                 "user_cake_day",
                 "post_karma",
                 "comment_karma"
                 )


class AllData:
    """All arguments required to write to the database"""
    __slots__ = PostDataDB.__slots__ + UserDataDB.__slots__
