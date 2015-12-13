#!/usr/bin/python

class MazeTiles(object):
    def __init__(self, mazeData):
        self.tileWidth = 9
        self.tileHeight = 9
        self.emptyTileChar = ' '
        self.wallTileChar = 'W'

        self.rows = len(mazeData)
        self.cols = self._calcRowWidth(mazeData[0])

        self._initTileArray(mazeData)

    def _calcRowWidth(self, mazeRow):
        width = 0

        for char in mazeRow:
            if char.isdigit():
                width += char
            else:
                width += 1

        return width

    def _initTileArray(self, mazeData):
        self.tiles = [None] * self.rows
        for i in range(self.rows):
            self.tiles[i] = [None] * self.cols

        insertRow = 0
        insertCol = 0

        for row in range(len(mazeData)):
            for col in range(len(mazeData[row])):
                if str(mazeData[row][col]).isdigit():
                    for i in range(mazeData[row][col]):
                        self.tiles[insertRow][insertCol] = self.emptyTileChar
                        insertCol += 1
                elif mazeData[row][col] == 'W':
                    self.tiles[insertRow][insertCol] = self.wallTileChar
                    insertCol += 1
                else:
                    self.tiles[insertRow][insertCol] = mazeData[row][col]
                    insertCol += 1

            insertRow += 1
            insertCol = 0

    def GetTileValueAtPosition(self, position):
        row, col = self.ConvertPositionToTile(position)
        return self.tiles[row][col]

    def GetTileValue(self, row, col):
        return self.tiles[row][col]

    def ConvertPositionToTile(self, position):
        col = int(position[0] / self.tileWidth)
        row = int(position[1] / self.tileHeight)

        return row, col

    def CalcStartPostionFromTile(self, row, col):
        x = 0
        y = 0

        x = (col * self.tileWidth) + self.tileWidth / 2
        y = (row * self.tileHeight) + self.tileHeight / 2

        return [x, y]

    def IsPositionInTileCenter(self, position):
        return self.IsPositionInTileHorizontalCenter(position) and \
            self.IsPositionInTileVerticalCenter(position)

    def IsPositionInTileVerticalCenter(self, position):
        return position[1] % self.tileHeight == self.tileHeight / 2

    def IsPositionInTileHorizontalCenter(self, position):
        return position[0] % self.tileWidth == self.tileWidth / 2

    def GetDistanceToTargetForDirection(self, direction, entity, target):
        distance = None

        entityRow, entityCol = self.ConvertPositionToTile(entity.position)
        targetRow, targetCol = self._findEntityLocation(target)

        xDistance = targetCol - entityCol
        yDistance = targetRow - entityRow

        if (direction == 'LEFT' and xDistance < 0) or \
           (direction == 'RIGHT' and xDistance > 0):
            distance = abs(xDistance)
        elif (direction == 'UP' and yDistance < 0) or \
             (direction == 'DOWN' and yDistance > 0):
            distance = abs(yDistance)

        return distance


    def GetNearestDirectionToTarget(self, entity, target):
        entityRow, entityCol = self.ConvertPositionToTile(entity.position)
        targetRow, targetCol = self._findEntityLocation(target)

        xDistance = targetCol - entityCol
        yDistance = targetRow - entityRow

        nearestIsX = abs(xDistance) < abs(yDistance)
        direction = 'RIGHT'

        if (nearestIsX or yDistance == 0) and xDistance < 0:
            direction = 'LEFT'
        elif (nearestIsX or yDistance == 0) and xDistance > 0:
            direction = 'RIGHT'
        elif yDistance < 0:
            direction = 'UP'
        elif yDistance > 0:
            direction = 'DOWN'

        return direction

    def GetPossibleDirections(self, entity):
        entityRow, entityCol = self._findEntityLocation(entity)

        possibleDirections = []

        if entityRow > 0 and self.GetTileValue(entityRow-1, entityCol) != self.wallTileChar:
            possibleDirections.append('UP')

        if entityRow < self.rows-1 and self.GetTileValue(entityRow+1, entityCol) != self.wallTileChar:
            possibleDirections.append('DOWN')

        if entityCol > 0 and self.GetTileValue(entityRow, entityCol-1) != self.wallTileChar:
            possibleDirections.append('LEFT')

        if entityCol < self.cols-1 and self.GetTileValue(entityRow, entityCol+1) != self.wallTileChar:
            possibleDirections.append('RIGHT')

        return possibleDirections

    def CheckIfEntitiesAreInLine(self, startEntity, endEntity):
        isInLine = False
        inLineDirection = None

        startRow, startCol = self._findEntityLocation(startEntity)
        endRow, endCol = self._findEntityLocation(endEntity)

        if startRow == endRow:
            isInLine = True
            if startCol < endCol:
                inLineDirection = 'RIGHT'
            else:
                inLineDirection = 'LEFT'

        elif startCol == endCol:
            isInLine = True
            if startRow < endRow:
                inLineDirection = 'DOWN'
            else:
                inLineDirection = 'UP'

        return isInLine, inLineDirection

    def HasLineOfSightToTarget(self, entity, target):
        hasLOSToTarget = False

        startRow, startCol = self._findEntityLocation(entity)
        endRow, endCol = self._findEntityLocation(target)

        if startRow == endRow and \
            self.IsPositionInTileVerticalCenter(entity.position):
            obstruction = False
            step = 1
            if startCol > endCol: step = -1
            for c in xrange(startCol, endCol, step):
                if self.GetTileValue(startRow, c) == self.wallTileChar:
                    obstruction = True

            if not obstruction:
                hasLOSToTarget = True

        elif startCol == endCol and \
            self.IsPositionInTileHorizontalCenter(entity.position):
            obstruction = False
            step = 1
            if startRow > endRow: step = -1
            for r in xrange(startRow, endRow, step):
                if self.GetTileValue(r, startCol) == self.wallTileChar:
                    obstruction = True

            if not obstruction:
                hasLOSToTarget = True

        return hasLOSToTarget

    def DirectionIsAwayFromTarget(self, direction, entity, target):
        awayFromTarget = False

        startRow, startCol = self._findEntityLocation(entity)
        endRow, endCol = self._findEntityLocation(target)

        if (direction == 'RIGHT' and startCol > endCol) or \
           (direction == 'LEFT' and startCol < endCol) or \
           (direction == 'UP' and startRow < endRow) or \
           (direction == 'DOWN' and startRow > endRow):
            awayFromTarget = True

        return awayFromTarget

    def _findEntityLocation(self, entity):
        row, col = self.ConvertPositionToTile(entity.position)

        return row, col

    def FindEntityPositionFromTiles(self, entityName):
        row = None
        col = None

        for i in range(len(self.tiles)):
            for j in range(len(self.tiles[i])):
                if self.tiles[i][j] == entityName:
                    row = i
                    col = j
                    break

        return self.CalcStartPostionFromTile(row, col)

    def BoundsCheckPosition(self, position):
        maxWidth = (self.cols + 1) * self.tileWidth
        maxHeight = (self.rows + 1) * self.tileHeight

        checkedPosition = position

        if position[0] < 0:
            checkedPosition[0] = 0
        if position[0] > maxWidth:
            checkedPosition[0] = maxWidth
        if position[1] < 0:
            checkedPosition[1] = 0
        if position[1] > maxHeight:
            checkedPosition[1] = maxHeight

        return checkedPosition

    def Update(self, entities):
        for i in range(self.rows):
            for j in range(self.cols):
                if self.tiles[i][j] != self.wallTileChar:
                    self.tiles[i][j] = self.emptyTileChar

        for entity in entities:
            newRow, newCol = self.ConvertPositionToTile(entity.position)

            if entity.id == 'G' and self.tiles[newRow][newCol] == self.emptyTileChar:
                self.tiles[newRow][newCol] = 'G'
            elif entity.id != 'G':
                self.tiles[newRow][newCol] = entity.id

    def DisplayTiles(self, teleporterPositions):
        for row in range(len(self.tiles)):
            rowString = ""
            for col in range(len(self.tiles[row])):
                teleporterHere = False
                thisPosition = self.CalcStartPostionFromTile(row, col)

                for T in teleporterPositions:

                    if T[0] == thisPosition[0] and \
                       T[1] == thisPosition[1]:
                       teleporterHere = True
                       break

                if teleporterHere and (self.GetTileValue(row, col) == self.emptyTileChar):
                    rowString += 'T'
                else:
                    rowString += str(self.tiles[row][col])
            print(rowString)
