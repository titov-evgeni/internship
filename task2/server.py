import json
import glob
import datetime

from typing import Union, List
from http.server import BaseHTTPRequestHandler, HTTPServer


class PostData:
    """Description of arguments required to write to the file"""

    __slots__ = ("UNIQUE_ID",
                 "post_url",
                 "user_name",
                 "user_karma",
                 "user_cake_day",
                 "post_karma",
                 "comment_karma",
                 "post_date",
                 "number_of_comments",
                 "number_of_votes",
                 "post_category")


class Files:
    """File handling methods"""

    @staticmethod
    def search_file():
        """Find file by mask

        Return "filename" if it was found.
        Return "None" if it was not found.
        """
        file_list = glob.glob('reddit*')
        if file_list:
            return file_list[0]
        else:
            return None

    @staticmethod
    def get_data_from_file(file_name: str):
        """Get data from file line by line

        Return list of posts data in dict format.
        Return empty list if there is no data file.
        """
        all_file_data = []
        if file_name:
            with open(f"{file_name}", encoding="utf-8-sig") as file:
                while True:
                    post_data_from_line = {}
                    line = file.readline()

                    if not line:
                        break
                    line_element = line.strip().split(";")

                    for num, arg in enumerate(PostData.__slots__):
                        post_data_from_line[arg] = line_element[num]
                        num += 1
                    all_file_data.append(post_data_from_line)
        return all_file_data

    @staticmethod
    def write_data_to_file(file_name: str, post_data_to_write: dict):
        """Get data values from post data dict and write down it to file"""
        list_data_values = []
        for attribute in PostData.__slots__:
            list_data_values.append(str(post_data_to_write[attribute]))

        with open(f"{file_name}", "a", encoding="utf-8-sig") as file:
            file.write(';'.join(list_data_values) + "\n")


class MyHandler(BaseHTTPRequestHandler):
    """The main http handler, routes requests by path
    and calls appropriate methods."""

    post_data_list = []
    count_data_to_write = len(PostData.__slots__)

    def check_file_data(self, file_name: str):
        """Check file data in variable 'post_data_list'.
        Get data from file if the 'post_data_list' is empty"""
        if not self.post_data_list:
            self.post_data_list = Files.get_data_from_file(
                file_name)

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
        """Check request data by "key" in PostData.__slots__

        Return "request_data" if data is correct.
        Return "None" if data is not correct.
        """
        count_request_data = 0
        for key in request_data:
            if key in PostData.__slots__:
                count_request_data += 1
        if count_request_data == self.count_data_to_write:
            return request_data
        else:
            return None

    def search_by_id_in_file_data(self, unique_id: str):
        """Search post data by id in file data

        Return posts data dict if it was found.
        Return "None" if it was not found.
        """
        for num, post_data in enumerate(self.post_data_list[:]):
            if post_data.get("UNIQUE_ID") == unique_id:
                return post_data
            else:
                num += 1
                if num == len(self.post_data_list):
                    return None

    def search_file_data_and_get_line_content_by_id(self, unique_id: str):
        """Sequence of actions to check file data,
        to get data by id from file data

        Return post data by id if it was found.
        Return "No data by unique_id" if post data by id was not found.
        Return list of all posts data in dict format, if unique id
        was not found.
        Return "None" if data file was not found.
        """
        file_name = Files.search_file()
        if file_name:
            self.check_file_data(file_name)
            if unique_id:
                line_content_by_id = self.search_by_id_in_file_data(unique_id)
                if line_content_by_id:
                    return line_content_by_id
                else:
                    return "No data by unique_id"
            else:
                return self.post_data_list
        else:
            return None

    def write_data_and_response(self,
                                file_name: str,
                                data: dict,
                                response_data: dict):
        """Sequence of actions to write down data to file
        and to generate a response"""
        Files.write_data_to_file(file_name, data)
        self.post_data_list.append(data)
        self.write_response_with_data(201, response_data)

    def overwrite_data_to_file(self, file_name: str):
        """Overwrite all posts data to file"""
        open(f"{file_name}", "w").close()
        for post in self.post_data_list:
            Files.write_data_to_file(file_name, post)

    def do_GET(self):
        """Process GET requests"""
        if self.path.startswith('/posts/'):
            self.send_response(200)
            self.end_headers()

            unique_id = self.get_unique_id_from_request_path(self.path)

            try:
                result = self.search_file_data_and_get_line_content_by_id(
                    unique_id)
                if isinstance(result, dict):
                    self.write_response_with_data(
                        200, result)
                elif isinstance(result, list):
                    self.write_response_with_data(200, self.post_data_list)
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
                result = self.search_file_data_and_get_line_content_by_id(
                    unique_id)
                if isinstance(result, dict):
                    file_name = Files.search_file()
                    self.post_data_list.remove(result)
                    self.overwrite_data_to_file(file_name)
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

            unique_id = post_data_dict.get("UNIQUE_ID")
            response_data["UNIQUE_ID"] = unique_id

            result = self.search_file_data_and_get_line_content_by_id(
                unique_id)
            if isinstance(result, dict):
                self.write_response_with_data(
                    409, {'error': 'wrong UNIQUE_ID'})
            elif isinstance(result, str):
                if len(post_data_dict) >= self.count_data_to_write:
                    if self.verification_of_request_data(post_data_dict):
                        file_name = Files.search_file()
                        self.write_data_and_response(
                            file_name, post_data_dict, response_data)
                    else:
                        self.write_response_with_data(
                            400, {'error': 'wrong data'})
                else:
                    self.write_response_with_data(
                        400, {'error': 'wrong data amount'})
            else:
                self.post_data_list.clear()
                if len(post_data_dict) >= self.count_data_to_write:
                    if self.verification_of_request_data(post_data_dict):
                        now = datetime.datetime.now().strftime('%Y%m%d%H%M')
                        self.write_data_and_response(f"reddit-{now}",
                                                     post_data_dict,
                                                     response_data)
                    else:
                        self.write_response_with_data(
                            400, {'error': 'wrong data'})
                else:
                    self.write_response_with_data(
                        400, {'error': 'wrong data amount'})
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
            new_unique_id = new_data_dict.get("UNIQUE_ID")

            try:
                result = self.search_file_data_and_get_line_content_by_id(
                    new_unique_id)

                if isinstance(result, dict):
                    self.write_response_with_data(
                        409, {'error': 'wrong UNIQUE_ID'})
                else:
                    unique_id = self.get_unique_id_from_request_path(
                        self.path)
                    if unique_id:
                        old_post_data = self.search_by_id_in_file_data(
                            unique_id)

                        if old_post_data:
                            file_name = Files.search_file()
                            for key in new_data_dict:
                                if key in old_post_data:
                                    old_post_data[key] = new_data_dict[key]

                            self.overwrite_data_to_file(file_name)
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
