class GameEngineException(Exception):
    pass

class InvalidMoveException(GameEngineException):
    def __init__(self, message):
        super().__init__(message)
class GameStateException(GameEngineException):
    pass


class ValidationException(GameEngineException):
    pass


class GameOverException(GameEngineException): 
    pass