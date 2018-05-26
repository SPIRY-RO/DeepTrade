def RunServer(environ, start_response):
    start_response('200 OK',[('Content-Type','text/html')])
    sb = bytes("<h1>Hello, web! </h1>", encoding = "utf8")
    return [sb]