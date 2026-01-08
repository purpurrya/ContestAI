class GameEngineException(Exception):
    pass

class InvalidMoveException(GameEngineException):
    def __init__(self,message: str):
        super().__init(message)
class GameStateException(GameEngineException):
    pass


class ValidationException(GameEngineException):
    pass


class GameOverException(GameEngineException): 
    pass