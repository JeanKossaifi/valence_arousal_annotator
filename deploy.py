from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from manage import app

http_server = HTTPServer(WSGIContainer(app))
# listen 55000 to 66000
http_server.listen(55557)
IOLoop.instance().start()
