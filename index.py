import wsgi_runner, pyt, logging

application = pyt.WSGIApplication('index.pyt', {})
def main(): wsgi_runner.run(application)
if __name__ == "__main__": main()
