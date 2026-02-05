import os.path

import tornado.web
import client_config
import traceback
from tornado.httpclient import AsyncHTTPClient
from tornado import httputil, httpclient
from tornado.web import RequestHandler, MissingArgumentError
import json
import logging
import asyncio
from typing import Any, Optional

class BaseHandler(RequestHandler):
    def __init__(
            self,
            application: "Application",
            request: httputil.HTTPServerRequest,
            **kwargs: Any
    ) -> None:
        self.user = None
        super().__init__(application, request, **kwargs)

    def set_default_headers(self) -> None:
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE, PATCH')
        self.set_header('Access-Control-Allow-Headers',
                        'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization')
        self.set_header('Server', 'PowerServer')

    def _prepare_headers(self) -> httputil.HTTPHeaders:
        headers = self.request.headers.copy()
        headers.pop("Host", None)
        return headers

    def _handle_response(self, response: httpclient.HTTPResponse) -> None:
        self.set_status(response.code)
        self._copy_response_headers(response)
        self.write(response.body)
        self.finish()

    def _copy_response_headers(self, response: httpclient.HTTPResponse) -> None:
        excluded_headers = {'Content-Length', 'Transfer-Encoding', 'Server'}
        for header in response.headers.get_all():
            if header[0] not in excluded_headers:
                self.set_header(header[0], header[1])

    def _handle_error(self, error: Exception) -> None:
        self.set_status(500)
        self.write(json.dumps({"error": str(error)}))
        self.finish()


    def get_arg(self, arg: str) -> Optional[str]:
        try:
            value = self.get_argument(arg)
        except MissingArgumentError:
            value = None
        if value == '':
            value = None
        logging.debug(f'get_argument:{arg}={value}')
        return value

    def get_dictarg(self) -> Any:
        return json.loads(self.request.body)

    def get_current_user(self):
        return None


class BasePageHandler(BaseHandler):
    need_login = False

    def write_error(self, status_code, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        if status_code == 403:
            logging.error(traceback.format_exc())
            self.redirect(client_config.error_url)
        else:
            # 其他错误的默认处理
            logging.error(traceback.format_exc())
            self.redirect(client_config.error_url)
            # super().write_error(status_code, **kwargs)

    async def get(self, *args, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        try:
            if self.__class__.need_login:
                _user = self.current_user
                if _user is None:
                    self.redirect(client_config.login_url)
                    return
            redirect_url = await asyncio.to_thread(self.myget, *args, **kwargs)
            if redirect_url is not None:
                self.redirect(redirect_url)
        except Exception as e:
            self.redirect('/pc/404')
            logging.error(e.__str__())
            logging.error(traceback.format_exc())

    async def post(self, *args, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        try:
            if self.__class__.need_login:
                _user = self.current_user
                if _user is None:
                    self.redirect(client_config.login_url)
                    return
            redirect_url = await asyncio.to_thread(self.mypost, *args, **kwargs)
            if redirect_url is not None:
                self.redirect(redirect_url)
        except Exception as e:
            self.redirect('/pc/404')
            logging.error(e.__str__())
            logging.error(traceback.format_exc())


class BaseApiHandler(BaseHandler):
    need_login = False

    def write_error(self, status_code, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        if status_code == 403:
            logging.error(traceback.format_exc())
            if 'exc_info' in kwargs and isinstance(kwargs['exc_info'], tuple) and len(kwargs['exc_info']) > 2 \
                    and isinstance(kwargs['exc_info'][1], tornado.web.HTTPError):
                errormsg = kwargs['exc_info'][1].log_message
            else:
                errormsg = 'System Error'
            _rtn = {'success': False,
                    'msg': 'failure: ' + errormsg,
                    }
            self.write(_rtn)
            return
        else:
            # 其他错误的默认处理
            # super().write_error(status_code, **kwargs)
            logging.error(str(kwargs))
            _rtn = {'success': False,
                    'msg': 'failure: System Error',
                    }
            self.write(_rtn)

    async def get(self, *args, **kwargs):
        try:
            logging.debug(self.__class__.__name__ + ":" + str(self.request))
            if self.__class__.need_login:
                _user = self.current_user
                if _user is None:
                    _rtn = {'success': False,
                            'msg': 'failure: Permission denied',
                            }
                    self.write(_rtn)
                    return
                api_path = self.request.uri
            await asyncio.to_thread(self.myget, *args, **kwargs)
        except Exception as e:
            _rtn = {'success': False,
                    'msg': 'failure: System Error',
                    }
            self.write(_rtn)
            logging.error(e.__str__())
            logging.error(traceback.format_exc())

    async def post(self, *args, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        try:
            if self.__class__.need_login:
                _user = self.current_user
                if _user is None:
                    _rtn = {'success': False,
                            'msg': 'failure: Permission denied',
                            }
                    self.write(_rtn)
                    return
                # api_path = args[0]
                api_path = self.request.path
                api_path = os.path.normpath(api_path)
            await asyncio.to_thread(self.mypost, *args, **kwargs)
        except Exception as e:
            _rtn = {'success': False,
                    'msg': 'failure: System Error',
                    }
            self.write(_rtn)
            logging.error(e.__str__())
            logging.error(traceback.format_exc())
