
import tornado.web

import config
import asyncio
from tornado.web import MissingArgumentError
from tornado.web import RequestHandler

import logging
import json
from tornado import httputil
from typing import Any
import traceback


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
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.set_header('Access-Control-Allow-Headers',
                        'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range')
        self.set_header('Server', 'PowerServer')

    async def get(self, *args, **kwargs):
        await asyncio.to_thread(self.myget, *args, **kwargs)

    def myget(self, *args, **kwargs):  # 所有子类需要实重载此方法，以实现异步操作
        raise Exception('No implement for myget method! ')

    def options(self):
        # Set status code to 204 (No Content)
        self.set_status(204)
        # End the response, no need to send a body
        self.finish()

    async def post(self, *args, **kwargs):  # 所有子类需要实重载此方法，以实现异步操作
        await asyncio.to_thread(self.mypost, *args, **kwargs)

    def mypost(self, *args, **kwargs):
        raise Exception('No implement for mypost method! ')

    def get_arg(self, arg: str):
        try:
            _value = self.get_argument(arg)
        except MissingArgumentError:
            _value = None
        if _value == '':
            _value = None
        # if isinstance(_value,str):
        #     _value = _value.encode().decode("unicode_escape")
        logging.debug('get_argument:%s=%s' % (arg, _value))
        return _value

    def get_dictarg(self):
        return json.loads(self.request.body)


class BasePageHandler(BaseHandler):
    need_login = True

    def write_error(self, status_code, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        self.set_status(status_code)
        if status_code == 403:
            logging.error(traceback.format_exc())
            self.redirect(config.error_url)
        else:
            # 其他错误的默认处理
            logging.error(traceback.format_exc())
            self.redirect(config.error_url)
            # super().write_error(status_code, **kwargs)

    async def get(self, *args, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        try:
            if self.__class__.need_login:
                _user = self.current_user
                if _user is None:
                    self.set_status(401)  # 未授权访问
                    self.redirect(config.login_url)
                    return
            redirect_url = await asyncio.to_thread(self.myget, *args, **kwargs)
            if redirect_url is not None:
                self.redirect(redirect_url)
        except Exception as e:
            self.set_status(500)  # 服务器内部错误
            self.redirect(config.error_url)
            logging.error(e.__str__())
            logging.error(traceback.format_exc())

    async def post(self, *args, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        try:
            if self.__class__.need_login:
                _user = self.current_user
                if _user is None:
                    self.set_status(401)  # 未授权访问
                    self.redirect(config.login_url)
                    return
            redirect_url = await asyncio.to_thread(self.mypost, *args, **kwargs)
            if redirect_url is not None:
                self.redirect(redirect_url)
        except Exception as e:
            self.set_status(500)  # 服务器内部错误
            self.redirect(config.error_url)
            logging.error(e.__str__())
            logging.error(traceback.format_exc())


class BaseApiHandler(BaseHandler):
    need_login = True

    def write_error(self, status_code, **kwargs):
        logging.debug(self.__class__.__name__ + ":" + str(self.request))
        self.set_status(status_code)
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
                    self.set_status(401)
                    self.write(_rtn)
                    return
            await asyncio.to_thread(self.myget, *args, **kwargs)
        except Exception as e:
            _rtn = {'success': False,
                    'msg': 'failure: System Error',
                    }
            self.set_status(403)
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
                    self.set_status(401)
                    self.write(_rtn)
                    return
            await asyncio.to_thread(self.mypost, *args, **kwargs)
        except Exception as e:
            _rtn = {'success': False,
                    'msg': 'failure: System Error',
                    }
            self.write(_rtn)
            self.set_status(403)
            logging.error(e.__str__())
            logging.error(traceback.format_exc())
