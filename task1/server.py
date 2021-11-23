import json

from typing import Union, List
from bson.objectid import ObjectId
from http.server import BaseHTTPRequestHandler, HTTPServer

from mongo import MongodbService

mongo = MongodbService()
db = mongo.create_db('PostsData')
posts_data = mongo.create_collection(db, 'posts')
users_data = mongo.create_collection(db, 'users')


class PostDataDB:
    """Description of post arguments required to write to the data base"""

    __slots__ = ("_id",
                 "post_url",
                 "post_date",
                 "number_of_comments",
                 "number_of_votes",
                 "post_category"
                 )


class UserDataDB:
    """Description of user arguments required to write to the data base"""

    __slots__ = ("user_name",
                 "user_karma",
                 "user_cake_day",
                 "post_karma",
                 "comment_karma"
                 )


class AllData:
    """All arguments required to write to the data base"""

    __slots__ = PostDataDB.__slots__ + UserDataDB.__slots__


class MyHandler(BaseHTTPRequestHandler):
    """The main http handler, routes requests by path
    and calls appropriate methods."""

    count_data_to_write = len(AllData.__slots__)

    @staticmethod
    def get_unique_id_from_request_path(path: str):
        """Get unique id from request path

        Return "unique_id" in str format if it was found.
        Return "None" if it was not found.
        """
        path_parts = path.split("/")
        unique_id = path_parts[2]
        if unique_id:
            return unique_id
        else:
            return None

    def verification_of_request_data(self, request_data: dict):
        """Check request data by "key" in AllData.__slots__

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
    def post_data_from_request_data(request_data: dict, user_data: dict):
        """Get post data by "key" in PostDataDB.__slots__

        Add "user_id" field to connect to user in "users" collection.
        Return post data in dict format.
        """
        post_data_for_db = {}
        for attribute in PostDataDB.__slots__:
            if attribute in request_data:
                post_data_for_db[attribute] = str(request_data[attribute])
        post_data_for_db["user_id"] = user_data["_id"]
        return post_data_for_db

    @staticmethod
    def user_data_from_request_data(request_data: dict):
        """Get user data by "key" in UserDataDB.__slots__

        Return user_data in dict format.
        """
        user_data_for_db = {}
        for attribute in UserDataDB.__slots__:
            if attribute in request_data:
                user_data_for_db[attribute] = str(request_data[attribute])
        return user_data_for_db

    def get_data_from_db(self, unique_id: str):
        """Sequence of actions to get data from data base

        Return all data by id if it was found.
        Return "No data by unique_id" if post data by id was not found.
        Return list of posts and users data in dict format, if unique id
        was not found.
        """
        try:
            if unique_id:
                all_data_by_id = {}
                post_data_by_id = mongo.find_one(posts_data,
                                                 {"_id": unique_id})
                if post_data_by_id:
                    all_data_by_id = self.get_user_data_from_db(
                        post_data_by_id)
                if all_data_by_id:
                    return all_data_by_id
                else:
                    return "No data by unique_id"
            else:
                list_all_data_from_db = []
                posts_data_from_db = mongo.find(posts_data)
                for post_data in posts_data_from_db:
                    all_data_from_document = self.get_user_data_from_db(
                        post_data)
                    list_all_data_from_db.append(all_data_from_document)
                return list_all_data_from_db
        except Exception:
            self.write_response(500)

    def get_user_data_from_db(self, post_data: dict):
        """Get user data from data base by id for specific post.

        Return dict of post and user data.
        """
        try:
            all_data = {}
            if "user_id" in post_data:
                user_id = post_data["user_id"]
                user_data_by_id = mongo.find_one(users_data,
                                                 {"_id": ObjectId(user_id)},
                                                 {"_id": False})
                post_data.pop("user_id", None)
                all_data.update(post_data)
                all_data.update(user_data_by_id)
            return all_data
        except Exception:
            self.write_response(500)

    def write_data_and_response(self, data: dict, response_data: dict):
        """Sequence of actions to write down data to data base
        and to generate a response"""
        try:
            mongo.insert_one(posts_data, data)
            self.write_response_with_data(201, response_data)
        except Exception:
            self.write_response(500)

    def process_new_user_data_from_PUT_request(self, new_post_data: dict,
                                               new_user_data: dict,
                                               unique_id: str):
        """Sequence of actions to process user data from PUT request"""
        try:
            if "user_name" in new_user_data:
                new_user_name = mongo.find_one(
                    users_data,
                    {"user_name": new_user_data["user_name"]})
                if not new_user_name:
                    self.update_post_and_user_document(new_post_data,
                                                       new_user_data,
                                                       unique_id)
                else:
                    self.write_response_with_data(400,
                                                  {'error': 'user exists'})
            else:
                self.update_post_and_user_document(new_post_data,
                                                   new_user_data,
                                                   unique_id)
        except Exception:
            self.write_response(500)

    def update_post_and_user_document(self, new_post_data: dict,
                                      new_user_data: dict,
                                      unique_id: str):
        """Sequence of actions to update post and user data
        and to generate a response"""
        try:
            mongo.update_one(users_data, {'_id': new_post_data["user_id"]},
                             new_user_data)
            new_post_data.pop("user_id", None)
            if new_post_data:
                mongo.update_one(posts_data, {'_id': unique_id},
                                 new_post_data)
            self.write_response(200)
        except Exception:
            self.write_response(500)

    def insert_user_data_to_db(self, data_for_db: dict):
        """Sequence of actions to write down user data to data base

        Return dict of inserted user data.
        """
        try:
            user_data = self.user_data_from_request_data(data_for_db)
            mongo.insert_one(users_data, user_data)
            user = mongo.find_one(users_data,
                                  {"user_name": data_for_db["user_name"]})
            return user
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
                if isinstance(result, dict):
                    self.write_response_with_data(200, result)
                elif isinstance(result, list):
                    self.write_response_with_data(200, result)
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
                if isinstance(result, dict):
                    post_content_by_id = mongo.find_one(posts_data,
                                                        {"_id": unique_id})
                    user_id = post_content_by_id["user_id"]
                    mongo.delete_one(posts_data, {"_id": unique_id})

                    # Check to delete user data
                    post_content_by_user_id = mongo.find_one(
                        posts_data, {"user_id": user_id})
                    if not post_content_by_user_id:
                        mongo.delete_one(users_data, {"_id": user_id})
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
            unique_id = str(post_data_dict.get("_id"))
            if unique_id:
                response_data["_id"] = unique_id
                result = self.get_data_from_db(unique_id)
                if isinstance(result, dict):
                    self.write_response_with_data(409, {'error': 'wrong _id'})
                elif isinstance(result, str):
                    if len(post_data_dict) >= self.count_data_to_write:
                        data_for_db = self.verification_of_request_data(
                            post_data_dict)
                        if data_for_db:
                            try:
                                user = mongo.find_one(
                                    users_data,
                                    {"user_name": data_for_db["user_name"]})
                                if not user:
                                    user = self.insert_user_data_to_db(
                                        data_for_db)
                                post_data = self.post_data_from_request_data(
                                    data_for_db, user)
                                self.write_data_and_response(post_data,
                                                             response_data)
                            except Exception:
                                self.write_response(500)
                        else:
                            self.write_response_with_data(
                                400, {'error': 'wrong data'})
                    else:
                        self.write_response_with_data(
                            400, {'error': 'wrong data amount'})
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
            new_unique_id = new_data_dict.get("_id")
            try:
                if new_unique_id:
                    self.write_response_with_data(
                        400, {'error': 'can not change _id'})
                else:
                    unique_id = self.get_unique_id_from_request_path(
                        self.path)
                    if unique_id:
                        old_post_data = self.get_data_from_db(unique_id)
                        if old_post_data:
                            user = mongo.find_one(
                                users_data,
                                {"user_name": old_post_data["user_name"]})
                            new_post_data = self.post_data_from_request_data(
                                new_data_dict, user)
                            new_user_data = self.user_data_from_request_data(
                                new_data_dict)
                            if new_user_data:
                                self.process_new_user_data_from_PUT_request(
                                    new_post_data, new_user_data, unique_id)
                            else:
                                new_post_data.pop("user_id", None)
                                mongo.update_one(posts_data,
                                                 {'_id': unique_id},
                                                 new_post_data)
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
        """Сreate response as status"""
        self.send_response_only(status)
        self.end_headers()

    def write_response_with_data(self, status: int,
                                 data: Union[dict, List[dict]]):
        """Сreate response with data as json"""
        body = json.dumps(data, indent=4).encode('utf-8')
        self.write_response(status)
        self.wfile.write(body)
        self.wfile.flush()


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 8087), MyHandler)
    server.serve_forever()

