#########################################################################
#  Matheus Fillipe -- 13, December of 2020                              #
#                                                                       #
#########################################################################
#  Description: A very simple and inefficient wrapper around basic      #
#  sqlite queries that are normally used. Don't use this module for     #
#  large projects big loops etc.                                        #
#                                                                       #
#########################################################################
#  Depends on: sqlite module, basically all python std.                 #
#                                                                       #
#########################################################################

import sqlite3
from pathlib import Path
from copy import copy


class DB():
    def __init__(self, dbFilePath, tableName, rowLabels, keepOpen=False):
        '''dbFilePath: str. Path for the file to save the sqtile db on.
           tableName: str. Name of the table to use. 
           rowLabels: list. Strings with the data keys to store, columns of the table. 
           keepOpen: bool. If set to True you will have to manually call connect and close. 
        '''
        self.filepath = dbFilePath
        self.tableName = tableName
        self.rowLabels = rowLabels
        self.keepOpen = True
        self.checkIfExistsIfNotCreate()

    def toDict(self, data):
        """toDict. Returns a dict.

        :param data: list which represents a full row to convert to a dict with the respective kes defined in rowLabels
        """
        return {n: data[i] for i, n in enumerate(self.rowLabels)}

    def toDictWithId(self, data):
        """toDictWithId. Returns a dict with the "id" field.

        :param data: list which represents a full row to convert to a dict with the respective kes defined in rowLabels
        """
        return {n: data[i] for i, n in enumerate(["id"]+self.rowLabels)}

    def toList(self, data):
        """toList. Converts a dict to a row list in the other defined by rowLabels

        :param data: dict. 
        """
        return [data[n] if n in data.keys() else "" for n in self.rowLabels]

    def checkIfExistsIfNotCreate(self):
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM "+self.tableName)
            col_name_list = [tuple[0] for tuple in self.cursor.description]
            col_name_list.remove('id')
        except:
            col_name_list = []
        self.close()
        if not sorted(col_name_list) == sorted(self.rowLabels):
            self.deleteTable()
            self._connect()
            self.cursor.execute("CREATE TABLE IF NOT EXISTS " + self.tableName +
                                " (id INTEGER primary key AUTOINCREMENT," + str(self.rowLabels)[1:-1] + ")")
            self.close()


    def connect(self):
        self.connection = sqlite3.connect(self.filepath)
        self.cursor = self.connection.cursor()
        self.connected = True

    def _connect(self):
        if self.keepOpen:
            return
        self.connect()

    def close(self):
        self.connection.commit()
        self.connection.close()
        self.connected = False

    def _close(self):
        if self.keepOpen:
            return
        self.close()

    def _daveData(self, dado):
        dado = self.toList(dado)
        self.cursor.execute("INSERT INTO "+self.tableName+" ("+str(self.rowLabels)[
                            1:-1] + ")VALUES (" + (len(self.rowLabels)*"?,")[:-1]+")", dado)

    def newData(self, dado):
        # assert len(dado)==len(self.rowLabels), "ERRO: O dado deve ter o tamanho " + str(len(self.rowLabels))
        self._connect()
        self._daveData(dado)
        id = copy(self.cursor.lastrowid)
        self._close()
        return id

    def saveDataList(self, lista):
        self._connect()
        [self._daveData(dado) for dado in lista]
        self._close()

    def _getData(self, id):
        return self.toDict(list(list(self.cursor.execute("SELECT * FROM " + self.tableName + " WHERE id = ?", (id,)))[0])[1:])

    def getData(self, id):
        self._connect()
        dado = self._getData(id)
        self._close()
        return dado

    def getDataWithId(self, id):
        self._connect()
        dado = self._getData(id)
        self._close()
        dado.update({"id": id})
        return dado

    def getAll(self):
        self._connect()
        dados = [self.toDict(row[1:]) for row in self.cursor.execute(
            "SELECT * FROM " + self.tableName)]
        self._close()
        return dados

    def getAllWithId(self):
        self._connect()
        dados = [self.toDictWithId(row) for row in self.cursor.execute(
            "SELECT * FROM " + self.tableName)]
        self._close()
        return dados

    def findData(self, key, nome):
        func = str
        try:
            float(nome)
            func = float
        except:
            pass
        self._connect()
        if type(nome) == str:
            key = key
            idList = [[list(dado)[0], self.toDict(list(dado)[1:])[key]]
                      for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName))
                      if nome.lower() in str(self.toDict(list(dado)[1:])[key]).lower()]
        else:
            idList = [[list(dado)[0], self.toDict(list(dado)[1:])[key]]
                      for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName))
                      if str(nome) == str(self.toDict(list(dado)[1:])[key])]
        self._close()
        try:
            return [x[0] for x in sorted(idList, key=lambda x: func(x[1]))]
        except ValueError as e:
            return [x[0] for x in sorted(idList, key=lambda x: str(x[1]))]

    def findExactMatchFromKey(self, key, nome):
        func = str
        try:
            float(nome)
            func = float
        except:
            pass
        self._connect()
        if type(nome) == str:
            key = key
            idList = [[list(dado)[0], self.toDict(list(dado)[1:])[key]]
                      for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName))
                      if nome.lower() == str(self.toDict(list(dado)[1:])[key]).lower()]
        else:
            idList = [[list(dado)[0], self.toDict(list(dado)[1:])[key]]
                      for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName))
                      if str(nome) == str(self.toDict(list(dado)[1:])[key])]
        self._close()
        try:
            return [x[0] for x in sorted(idList, key=lambda x: func(x[1]))]
        except ValueError as e:
            return [x[0] for x in sorted(idList, key=lambda x: str(x[1]))]

    def getDataListByIdList(self, listaDeIds):
        return [self.getData(id) for id in listaDeIds]

    def getDataListByIdListWithId(self, listaDeIds):
        return [self.getDataWithId(id) for id in listaDeIds]

    def findDataByKey(self, key, nome):
        return sorted(self.getDataListByIdList(self.findData(key, nome)), key=lambda x: x[key])

    def findGreaterThan(self, key, valor):
        assert type(valor) == int or type(
            valor) == float, "Entre com valores numéricos"
        self._connect()
        idList = [[list(dado)[0], self.toDict(list(dado)[1:])[key]]
                  for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName))
                  if float(valor) <= float(self.toDict(list(dado)[1:])[key])]
        self._close()
        return [x[0] for x in sorted(idList, key=lambda x: x[1])]

    def findLessThan(self, key, valor):
        assert type(valor) == int or type(
            valor) == float, "Entre com valores numéricos"
        self._connect()
        idList = [[list(dado)[0], self.toDict(list(dado)[1:])[key]]
                  for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName))
                  if float(valor) >= float(self.toDict(list(dado)[1:])[key])]
        self._close()
        return [x[0] for x in sorted(idList, key=lambda x: x[1])]

    def findDataBiggerThan(self, key, valor):
        return sorted(self.getDataListByIdList(self.findGreaterThan(key, valor)), key=lambda x: x[key])

    def findDataLessThan(self, key, valor):
        return sorted(self.getDataListByIdList(self.findLessThan(key, valor)), key=lambda x: x[key])

    def deleteData(self, id):
        self._connect()
        id = str(id)
        self.cursor.execute(
            "DELETE FROM " + self.tableName + " WHERE ID = ?", (id,))
        self._close()

    def update(self, id, dado):
        """updates given id to new dict
        :param id: id to modify
        :param dado: data dict that can only contain fields to update
        """
        d = self.getData(id)
        d.update(dado)
        d = self.toList(d)
        self._connect()
        self.cursor.execute("UPDATE " + self.tableName + " SET " + " = ?,".join(self.rowLabels) + "= ? WHERE id= ?",
                            (d+[id]))
        self._close()

    def deleteTable(self):
        """Deletes the table"""
        self._connect()
        self.cursor.execute("DROP TABLE IF EXISTS " + self.tableName)
        self._close()

    def deleteAll(self):
        """Deletes the db file"""
        Path(self.filepath).unlink()


