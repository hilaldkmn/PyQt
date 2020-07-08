from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class Connection(object): #iki blok item arasında bağlantı çizgisini oluşturmak içindir
   """
    - fromPort
    - toPort
   """
   def __init__(self, fromPort, toPort):
      self.fromPort = fromPort
      self.pos1 = None
      self.pos2 = None
      if fromPort:
         self.pos1 = fromPort.scenePos()
         fromPort.posCallbacks.append(self.setBeginPos)
      self.toPort = toPort
      # Create arrow item:
      self.arrow = ArrowItem()
      editor.diagramScene.addItem(self.arrow) 
   def setFromPort(self, fromPort): # bağlantı başlangıç portu 
      self.fromPort = fromPort
      if self.fromPort:
         self.pos1 = fromPort.scenePos()
         self.fromPort.posCallbacks.append(self.setBeginPos)
   def setToPort(self, toPort): # bağlantı bitiş portu
      self.toPort = toPort
      if self.toPort:
         self.pos2 = toPort.scenePos()
         self.toPort.posCallbacks.append(self.setEndPos)
   def setEndPos(self, endpos): # bağlantı bitiş pozisyonu
      self.pos2 = endpos
      self.arrow.setLine(QtCore.QLineF(self.pos1, self.pos2))
   def setBeginPos(self, pos1): # bağlantı başlangıç pozisyonu
      self.pos1 = pos1
      self.arrow.setLine(QtCore.QLineF(self.pos1, self.pos2))
   def delete(self):
      editor.diagramScene.removeItem(self.arrow)
      # Remove position update callbacks:


class ArrowItem(QtWidgets.QGraphicsLineItem):  #bağlantı çizgisinin görselleştirilmesi içindir
    def __init__(self):
        super().__init__(None)
        self.setPen(QtGui.QPen(QtCore.Qt.red,2))
        self.setFlag(self.ItemIsSelectable,True)
    def x(self):
        pass


class PortItem(QtWidgets.QGraphicsEllipseItem): #bağlantı noktaları tanımlanması içindir
    """ Represents a port to a subsystem """
    def __init__(self, name, parent=None):
        super().__init__(QtCore.QRectF(-6,-6,12.0,12.0), parent) 
        self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor)) # fare üzerine geldiğinmde imleç(cursor) artı işaretini alır
        # Properties:
        self.setBrush(QtGui.QBrush(QtCore.Qt.red))
        # Name:
        self.name = name
        self.posCallbacks = []
        self.setFlag(self.ItemSendsScenePositionChanges, True)

    def itemChange(self, change, value):  
        if change == self.ItemScenePositionHasChanged:
            for cb in self.posCallbacks:
                cb(value)
            return value
        return super().itemChange(change, value)

    def mousePressEvent(self, event): # porta tıklandığında bağlantı oluşturulmaktadır
        editor.startConnection(self)



class HandleItem(QtWidgets.QGraphicsEllipseItem):
    """Fare tarafından taşınabilen bir tutamaç"""
    def __init__(self,parent=None):
        super().__init__(QtCore.QRectF(-4.0,-4.0,8.0,8.0),parent) #item ım oluşturulması
        self.posChangeCallbacks=[]
        self.setBrush(QtGui.QBrush(QtCore.Qt.white))
        self.setFlag(self.ItemIsMovable,True)         #item a hareket etme özelliği eklenmektedir
        self.setFlag(self.ItemSendsGeometryChanges,True)  # item deki değişikleri okunabilmesi için aktive edilmelidir
        self.setCursor(QtGui.QCursor(QtCore.Qt.SizeFDiagCursor))
   
    def itemChange(self, change, value): #handleitem'de ki değişiklik olduğu zaman çalışan ön tanımlı methodtur
        if change==self.ItemPositionChange:
            x,y=value.x(),value.y()
            for cb in self.posChangeCallbacks:
                res=cb(x,y)
                if res:
                    x,y=res 
                    value=QtCore.QPoint(x,y)
            return value
        return super().itemChange(change,value)
  


class BlockItem(QtWidgets.QGraphicsRectItem):  # qgraphicsScene'e dikdörtgen şekli eklemek içindir
   
    """
    Diyagramdaki bir bloğu temsil eder
    X ve y ve genişlik ve yüksekliğe sahiptir
    genişlik ve yükseklik sadece sağ alt köşedeki bir uç ile ayarlanabilir.

    -in ve çıkış portları
    -parameters
    -açıklama
    """
    def __init__(self,name='Untitled',parent=None):
        super().__init__(parent)
        w=60.0
        h=40.0
        #Properties of the rectangle
        self.setPen(QtGui.QPen(QtCore.Qt.blue, 2))     #kalem tipini belirler
        self.setBrush(QtGui.QBrush(QtCore.Qt.lightGray)) #fırça tipini belirler
        self.setFlags(self.ItemIsSelectable|self.ItemIsMovable)  #seçilebilir ve hareket ettirebilirlik özellikleri tanımlanır
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor)) #cursor tipi belirlenir
        #Label
        self.label=QtWidgets.QGraphicsTextItem(name,self)
        #Create corner for resize
        self.sizer=HandleItem(self)     #içinde ki kutuyu yani büyütüp küçültmeyi çizer
        self.sizer.setPos(w,h) #sizer item ını  block item ının sağ alt köşesine yerleştirir 
        self.sizer.posChangeCallbacks.append(self.changeSize) #Connect the callback  
        self.sizer.setVisible(True)  # yeni kutumuz oluştuğunda sizer görünür hale getirir
        self.sizer.setFlag(self.sizer.ItemIsSelectable,True)  #size seçilebilir hale getirir
        #Inputs and Outputs of the block:
        if name=='Pressure': #yeni yapılan kutu ismi pressure ise tek bağlantı noktalı
            self.inputs=[]
            self.outputs = []
            self.outputs.append( PortItem('Arm1', self) )
        if name=='K Loss': #yeni yapılan kutu diğeri ise bağlantı noktası iki tanedir
            self.inputs=[]
            self.inputs.append( PortItem('Arm1', self) )
            self.outputs = []
            self.outputs.append( PortItem('Arm2', self) )

        # Update size:
        self.changeSize(w, h)

    def changeSize(self, w, h):  # block item ının boyutlarının belirlenmesi, içindeki yazının konumunun belirlenmesi
                                #ve bağlantı noktalarının yerlerinin belirlenmesi için kullanılır
      """ Resize block function """ # ve 
      # Limit the block size:
      if h < 20:
         h = 20
      if w < 40:
         w = 40
      if h > 50:
         h = 50
      if w > 100:
         w = 100
      self.setRect(0.0, 0.0, w, h)
      # center label:
      rect = self.label.boundingRect()
      lw, lh = rect.width(), rect.height()
      lx = (w - lw) / 2
      ly = (h - lh) / 2
      self.label.setPos(lx, ly)
      # Update port positions:
      if len(self.inputs) == 1:
         self.inputs[0].setPos(-4, h / 2)
      elif len(self.inputs) > 1:
         y = 5
         dy = (h - 10) / (len(self.inputs) - 1)
         for inp in self.inputs:
            inp.setPos(-4, y)
            y += dy
      if len(self.outputs) == 1:
         self.outputs[0].setPos(w+4, h / 2)
      elif len(self.outputs) > 1:
         y = 5
         dy = (h - 10) / (len(self.outputs) + 0)
         for outp in self.outputs:
            outp.setPos(w+4, y)
            y += dy

      return w, h



class DiagramScene(QtWidgets.QGraphicsScene):
    def __init__(self,parent=None):
        super().__init__(parent) 
    def mouseMoveEvent(self, mouseEvent):  #farenin hareketini algılayan eventtir
        editor.sceneMouseMoveEvent(mouseEvent) # event bilgileri mauseevent argümanında tutulmaktadır
        super().mouseMoveEvent(mouseEvent),
    def mouseReleaseEvent(self, mouseEvent): #farenin bırakıldığında aktif olan eventtir
        editor.sceneMouseReleaseEvent(mouseEvent)
        super().mouseReleaseEvent(mouseEvent)



class EditorGraphicsView(QtWidgets.QGraphicsView): # Qgraphicsscene objesinin ekranda görüntülenmesi için kullanılmaktadır
    """
    The  QGraphicsView class provides a widget for displaying the contents of a QGraphicsScene 
    
    scene = QGraphicsScene()
    scene.addText("Hello, world
    view = QGraphicsView(scene)
    view.show()
    """
    def __init__(self,scene,parent=None):
        super().__init__(scene,parent)
    def dragEnterEvent(self, event): #	Sürükleme eylemi gerçekleştiğinde çalışan event
        if event.mimeData().hasFormat('component'):
            event.accept()
    def dragMoveEvent(self, event): #Sürükleme eylemi gerçekleşirken çalışan event
        if event.mimeData().hasFormat('component'):
            event.accept()
    def dropEvent(self, event): #Bırakma eylemi gerçekleştiğinde çalışan event
        if event.mimeData().hasFormat('component'):
            event.accept()
            name=event.mimeData().data('component').data().decode('utf-8')
            b1=BlockItem(name)  #grafik sahnesi için item oluşturur
            b1.setPos(self.mapToScene(event.pos())) #item pozisyonunu belirlenir
            self.scene().addItem(b1)  #oluşturulan item grafik sahnesine eklenir



class LibraryModel(QtGui.QStandardItemModel): #data tipini belirler kendi tipinde bir  data verir
    def __init__(self, parent=None):
        super().__init__(parent)
    def mimeTypes(self): #data tipini geri döndürür
        return ['component']
    def mimeData(self,idxs):  #data objesini geri döndürür sonra data objesi sürükle bırak işlemlerinde kullanılmaktadır
        mimedata=QtCore.QMimeData()
        for idx in idxs:
            if idx.isValid():
                txt=self.data(idx,QtCore.Qt.DisplayRole)
                mimedata.setData('component',QtCore.QByteArray(bytes(txt,'utf-8')))
                #print(str(mimedata.data('component').data().decode('utf-8')))
            return mimedata



class DiagramEditor(QtWidgets.QWidget):
    def __init__(self,parent=None):
        #super(DiagramEditor,self).__init__(parent)
        super().__init__(parent)
        self.setWindowTitle('Diagram Editor')

         #widget layout and child widgets
        self.horizontalLayout=QtWidgets.QHBoxLayout(self)
        self.libraryBrowserView=QtWidgets.QListView(self)
        self.libraryBrowserView.setMaximumWidth(150)
        self.libraryModel=LibraryModel(self)
        self.libraryModel.setColumnCount(2) #2 eşit parçaya böl

        #create an icon with an icon
        pixmap=QtGui.QPixmap(60,60) #yapılacak şekillerin arka planda ne kadar yer kaplanacağı belirlenir
        pixmap.fill()               #içi doldurulur
        painter=QtGui.QPainter(pixmap)       #boyama işlemi ve sonrasında da yapılacak şekiller tanımlandırılır ve konumlandırılır
        painter.fillRect(10,10,40,40,QtCore.Qt.blue)
        painter.setBrush(QtCore.Qt.red)
        painter.drawEllipse(36,2,20,20)
        painter.setBrush(QtCore.Qt.yellow)
        painter.drawEllipse(20,20,20,20)
        painter.end()

        self.libItems=[]
        self.libItems.append(QtGui.QStandardItem(QtGui.QIcon(pixmap),'Pressure'))  #kütüphaneye bileşen eklenir
        self.libItems.append(QtGui.QStandardItem(QtGui.QIcon(pixmap),'K Loss'))
        for i in self.libItems:
            self.libraryModel.appendRow(i)
                
        self.libraryBrowserView.setModel(self.libraryModel)                        #hepsine data tipi belirlenir
        self.libraryBrowserView.setViewMode(self.libraryBrowserView.IconMode)      #icon modunda gösterir
        self.libraryBrowserView.setDragDropMode(self.libraryBrowserView.DragOnly)  #sadece sürüklemeye izin verir
        self.horizontalLayout.addWidget(self.libraryBrowserView)                #layout a listview widget ı eklenir
    #####
        self.diagramScene=DiagramScene(self) #çizim sahnesini oluşturur
        self.diagramView=EditorGraphicsView(self.diagramScene,self) #çizim sahnesinin gösterildiği widget
        self.horizontalLayout.addWidget(self.diagramView) # çizim alanı layout a eklenir

        self.startedConnection = None

    def startConnection(self, port):   #başlangıç noktasını algılamak içindir
        self.startedConnection = Connection(port, None)
    def sceneMouseMoveEvent(self, event):  # mouse hareketine göre bağlantı çizgisini güncellemektedir
        if self.startedConnection:
            pos = event.scenePos()
            self.startedConnection.setEndPos(pos)
    def sceneMouseReleaseEvent(self, event):  # bitiş portu il bağlantı tanımlanır
        # Clear the actual connection:
        if self.startedConnection:
            pos = event.scenePos()
            items = self.diagramScene.items(pos)
            for item in items:
                if type(item) is PortItem:
                    self.startedConnection.setToPort(item)
            if self.startedConnection.toPort == None:
                self.startedConnection.delete()
            self.startedConnection = None
        


if __name__=='__main__':
    app=QtWidgets.QApplication(sys.argv)
    global editor 
    editor=DiagramEditor()
    editor.show()
    editor.resize(700,800)
    sys.exit(app.exec_())

