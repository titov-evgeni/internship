"""Connect to database, routes requests by path and calls
appropriate methods"""
import sys
import json

from typing import Union, List
from http.server import BaseHTTPRequestHandler, HTTPServer

from db_connectors.postgres import PostgreService
import postgres_connect as connect
from data_description import PostDataDB, UserDataDB, AllData

try:
    db = 'posts_data'
    users = 'users'
    posts = 'posts'
    postgres = PostgreService("127.0.0.1", 5432)
    connection_to_db = connect.postgresql_create_connection_to_db(postgres, db)
except Exception:
    sys.exit()


class MyHandler(BaseHTTPRequestHandler):
    """The main http handler, routes requests by path
    and calls appropriate methods."""
    count_data_to_write = len(AllData.__slots__)
    count_post_data = len(PostDataDB.__slots__)

    @staticmethod
    def get_unique_id_from_request_path(path: str) -> Union[str, None]:
        """Get unique id from request path

        "path" - request path
        Return "unique_id" in str format if it was found.
        Return "None" if it was not found.
        """
        path_parts = path.split("/")
        unique_id = path_parts[2]
        if unique_id:
            return unique_id
        else:
            return None

    def verification_of_request_data(self,
                                     request_data: dict) -> Union[dict, None]:
        """Check request data by "key" in AllData.__slots__

        "request_data" - all data passed in the request
        Return "request_data" if data is correct.
        Return "None" if data is not correct.
        """
        count_request_data = 0
        data_for_db = {}
        for attribute in AllData.__slots__:
            if attribute in request_data:
                count_request_data += 1
                data_for_db[attribute] = request_data[attribute]
        if count_request_data == self.count_data_to_write:
            return data_for_db
        else:
            return None

    @staticmethod
    def post_data_from_request_data(request_data: dict, 
                                    user_data: tuple) -> dict:
        """Get post data by "key" in PostDataDB.__slots__

        "request_data" - all data passed in the request
        "user_data" -  user data from "users" collection
        Add "user_id" field to connect to user in "users" collection.
        Return post data in dict format.
        """
        post_data_for_db = {}
        for attribute in PostDataDB.__slots__:
            if attribute in request_data:
                post_data_for_db[attribute] = str(request_data[attribute])
        post_data_for_db["user_id"] = user_data[0]
        return post_data_for_db

    @staticmethod
    def user_data_from_request_data(request_data: dict) -> dict:
        """Get user data by "key" in UserDataDB.__slots__

        "request_data" - all data passed in the request
        Return user_data in dict format.
        """
        user_data_for_db = {}
        for attribute in UserDataDB.__slots__:
            if attribute in request_data:
                user_data_for_db[attribute] = str(request_data[attribute])
        return user_data_for_db

    @staticmethod
    def data_for_response(list_data: list) -> Union[dict, List[dict]]:
        """Transform post and user database data in dict format for response

        "list_data" - list of post and user data for response
        Return data in dict format if there is one entry in the "list_data".
        Return data in list of dict format if there are many entry
        in the "list_data".
        """
        if isinstance(list_data[0], list):
            data_for_response = []
            for data in list_data:
                data_for_response.append(dict(zip(AllData.__slots__, data)))
            return data_for_response
        else:
            return dict(zip(AllData.__slots__, list_data))

    def get_data_from_db(self, unique_id: str) -> Union[list, str, None]:
        """Sequence of actions to get data from data base

        "unique_id" - unique id of the row in the "posts" table
        Return all data by id if it was found.
        Return "No data by unique_id" if post data by id was not found.
        Return list of posts and users data in list format, if unique id
        was not found.
        """
        try:
            if unique_id:
                all_data_by_id = []
                post_data_by_id = self.get_unique_data_from_db(posts, "id",
                                                               unique_id)
                if post_data_by_id is None:
                    return None
                elif post_data_by_id:
                    all_data_by_id = self.get_user_data_from_db(post_data_by_id)
                if all_data_by_id:
                    return all_data_by_id
                else:
                    return "No data by unique_id"
            else:
                list_all_data_from_db = []
                posts_data_from_db = postgres.find_all(posts)
                for post_data in posts_data_from_db:
                    all_data_from_document = self.get_user_data_from_db(post_data)
                    list_all_data_from_db.append(all_data_from_document)
                return list_all_data_from_db
        except Exception:
            self.write_response(500)

    def get_unique_data_from_db(self, table_name: str, column: str,
                                value: str) -> Union[tuple, list, None]:
        """Get unique data from table by filter

        "table_name" - table name in database
        "column" - column name in the table
        "value" - filter to find row in the table
        Return unique data in tuple format or empty list if it was not found.
        """
        try:
            unique_data = postgres.find_unique_data(table_name, column,
                                                    {"value": value})
            if isinstance(unique_data, str):
                raise Exception
            else:
                return unique_data
        except Exception:
            self.write_response(500)

    def get_user_data_from_db(self, post_data: tuple) -> Union[list, None]:
        """Get user data from data base by id for specific post.

        "post_data" - post data from "posts" table
        Return concatenated post and user data in list format.
        """
        try:
            all_data = []
            if post_data:
                all_data = list(post_data)
                user_id = post_data[-1]
                user_data_by_id = self.get_unique_data_from_db(users, "id",
                                                               user_id)
                list_user_data = list(user_data_by_id)
                list_user_data.pop(0)
                all_data.pop(-1)
                all_data.extend(list_user_data)
            return all_data
        except Exception:
            self.write_response(500)

    def write_data_and_response(self, post_data: dict,
                                response_data: dict) -> None:
        """Sequence of actions to write down data to data base
        and to generate a response

        "post_data" - post data to insert into "posts" table
        "response_data" - request response data
        """
        try:
            data_values = []
            for attribute in PostDataDB.__slots__:
                data_values.append(str(post_data[attribute]))
            data_values.append((post_data["user_id"]))
            fields = PostDataDB.__slots__ + ("user_id",)
            postgres.insert_one(posts, fields, tuple(data_values))
            self.write_response_with_data(201, response_data)
        except Exception:
            self.write_response(500)

    def process_new_user_data_from_PUT_request(self, new_post_data: dict,
                                               new_user_data: dict,
                                               unique_id: str) -> None:
        """Sequence of actions to process user data from PUT request

        "new_post_data" - post data passed in the PUT request
        "new_user_data" - user data passed in the PUT request
        "unique_id" - unique id of the row in the "posts" table
        """
        try:
            if "user_name" in new_user_data:
                new_user_name = self.get_unique_data_from_db(users,
                                    "user_name", new_user_data["user_name"])
                if not new_user_name:
                    self.update_posts_and_users_tables(new_post_data,
                                                       new_user_data,
                                                       unique_id)
                else:
                    self.write_response_with_data(400, {'error': 'user exists'})
            else:
                self.update_posts_and_users_tables(new_post_data,
                                                   new_user_data,
                                                   unique_id)
        except Exception:
            self.write_response(500)

    def update_posts_and_users_tables(self, new_post_data: dict,
                                      new_user_data: dict,
                                      unique_id: str) -> None:
        """Sequence of actions to update post and user data
        and to generate a response

        "new_post_data" - post data passed in the PUT request
        "new_user_data" - user data passed in the PUT request
        "unique_id" - unique id of the row in the "posts" table
        """
        try:
            user_id = new_post_data["user_id"]
            user_fields = list(new_user_data.keys())
            user_data = list(new_user_data.values())
            user_data.append(user_id)
            postgres.update(users, user_fields, "id", user_data)
            new_post_data.pop("user_id", None)
            if new_post_data:
                post_fields = list(new_post_data.keys())
                post_data = list(new_post_data.values())
                post_data.append(unique_id)
                postgres.update(posts, post_fields, "id", post_data)
            self.write_response(200)
        except Exception:
            self.write_response(500)

    def insert_user_data_to_db(self, data_for_db: dict) -> Union[tuple, None]:
        """Sequence of actions to write down user data to data base

        "data_for_db" - all data passed in the request
        Return tuple of inserted user data.
        """
        try:
            data_values = []
            user_data = self.user_data_from_request_data(data_for_db)
            for attribute in UserDataDB.__slots__:
                data_values.append(str(user_data[attribute]))
            postgres.insert_one(users, UserDataDB.__slots__, tuple(data_values))
            new_user = self.get_unique_data_from_db(users, "user_name",
                                                    data_for_db["user_name"])
            return new_user
        except Exception:
            self.write_response(500)

    def do_GET(self):
        """Process GET requests"""
        if self.path.startswith('/posts/'):
            self.send_response(200)
            self.end_headers()
            unique_id = self.get_unique_id_from_request_path(self.path)
            try:
                result = self.get_data_from_db(unique_id)
                if isinstance(result, list):
                    response_data = self.data_for_response(result)
                    self.write_response_with_data(200, response_data)
                else:
                    raise Exception
            except Exception:
                self.write_response(404)
        else:
            self.write_response_with_data(400, {'error': 'wrong path'})

    def do_DELETE(self):
        """Process DELETE requests"""
        if self.path.startswith('/posts/'):
            self.send_response(200)
            self.end_headers()
            unique_id = self.get_unique_id_from_request_path(self.path)
            try:
                result = self.get_data_from_db(unique_id)
                if isinstance(result, list):
                    post_content_by_id = self.get_unique_data_from_db(posts,
                                                            "id", unique_id)
                    user_id = post_content_by_id[-1]
                    postgres.delete(posts, "id", {"value": unique_id})

                    # Check to delete user data
                    post_content_by_user_id = self.get_unique_data_from_db(posts,
                                                            "user_id", user_id)
                    if not post_content_by_user_id:
                        postgres.delete(users, "id", {"value": user_id})
                    self.write_response(200)
                else:
                    self.write_response(404)
            except Exception:
                self.write_response(404)
        else:
            self.write_response_with_data(400, {'error': 'wrong path'})

    def do_POST(self):
        """Process POST requests"""
        if self.path == "/posts/":
            self.send_response(201)
            self.end_headers()
            response_data = {}
            content_len = int(self.headers.get('Content-Length'))
            request_post_data = str(self.rfile.read(content_len
                                                    ).decode("utf-8-sig"))
            post_data_dict = json.loads(request_post_data)
            unique_id = str(post_data_dict.get("id"))
            if unique_id:
                response_data["id"] = unique_id
                result = self.get_data_from_db(unique_id)
                if isinstance(result, list):
                    self.write_response_with_data(409, {'error': 'wrong id'})
                elif result is None:
                    self.write_response(404)
                elif isinstance(result, str):
                    if len(post_data_dict) >= self.count_data_to_write:
                        data_for_db = self.verification_of_request_data(
                            post_data_dict)
                        if data_for_db:
                            user_data = self.get_unique_data_from_db(
                                users, "user_name", data_for_db["user_name"])
                            if not user_data:
                                user_data = self.insert_user_data_to_db(
                                    data_for_db)
                            post_data = self.post_data_from_request_data(
                                data_for_db, user_data)
                            self.write_data_and_response(post_data,
                                                         response_data)
                        else:
                            self.write_response_with_data(400,
                                                    {'error': 'wrong data'})
                    else:
                        self.write_response_with_data(400,
                                                {'error': 'wrong data amount'})
            else:
                self.write_response_with_data(400, {'error': 'wrong data'})
        else:
            self.write_response_with_data(400, {'error': 'wrong path'})

    def do_PUT(self):
        """Process PUT requests"""
        if self.path.startswith('/posts/'):
            self.send_response(200)
            self.end_headers()
            content_len = int(self.headers.get('Content-Length'))
            request_post_data = str(
                self.rfile.read(content_len).decode("utf-8-sig"))
            new_data_dict = json.loads(request_post_data)
            new_unique_id = new_data_dict.get("id")
            try:
                if new_unique_id:
                    self.write_response_with_data(400,
                                                  {'error': "can't change id"})
                else:
                    unique_id = self.get_unique_id_from_request_path(self.path)
                    if unique_id:
                        old_post_data = self.get_data_from_db(unique_id)
                        if old_post_data:
                            user_data = self.get_unique_data_from_db(users,
                                        "user_name",
                                        old_post_data[self.count_post_data])
                            new_post_data = self.post_data_from_request_data(
                                new_data_dict, user_data)
                            new_user_data = self.user_data_from_request_data(
                                new_data_dict)
                            if new_user_data:
                                self.process_new_user_data_from_PUT_request(
                                    new_post_data, new_user_data, unique_id)
                            else:
                                new_post_data.pop("user_id", None)
                                post_fields = list(new_post_data.keys())
                                post_data = list(new_post_data.values())
                                post_data.append(unique_id)
                                postgres.update(posts, post_fields, "id",
                                                post_data)
                                self.write_response(200)
                        else:
                            self.write_response(404)
                    else:
                        raise Exception
            except Exception:
                self.write_response(404)
        else:
            self.write_response_with_data(400, {'error': 'wrong path'})

    def write_response(self, status: int):
        """Create response as status"""
        self.send_response_only(status)
        self.end_headers()

    def write_response_with_data(self, status: int,
                                 data: Union[dict, List[dict]]):
        """Create response with data as json"""
        body = json.dumps(data, indent=4).encode('utf-8')
        self.write_response(status)
        self.wfile.write(body)
        self.wfile.flush()


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 8087), MyHandler)
    server.serve_forever()
