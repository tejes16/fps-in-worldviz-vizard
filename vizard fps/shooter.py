import viz
import vizcam
import vizact
import vizshape
import math

########################
#START SCREEN WITH TEXT#
########################
class StartScreen(viz.EventClass) :
	def __init__(self) :
		viz.mouse(viz.OFF)
		viz.EventClass.__init__(self)
		
		#Title Screen - disappears after user pushes RETURN
		self.title = viz.addText3D('Press Enter to Start')
		self.title.color(viz.BLACK)
		self.title.font('COURIER NEW')
		
		#Boolean set true after the title disappears
		self.mapSelect = False
		
		#Map 1: Shipment
		self.shipment = viz.addText3D('Shipment')
		self.shipment.color(viz.BLACK)
		self.shipment.font('COURIER NEW')
		
		mat = viz.Matrix()
		mat.postTrans(-11,3,25)
		self.title.setMatrix(mat)
		
		self.shipment.setMatrix(mat)
		self.shipment.visible( viz.OFF )
		
		#Map 2: 
		self.factory = viz.addText3D('Factory')
		self.factory.color(viz.BLACK)
		self.factory.font('COURIER NEW')
		
		mat = viz.Matrix()
		mat.postTrans(0,3,25)
		
		self.factory.setMatrix(mat)
		self.factory.visible( viz.OFF )
		
		#Instructions
		self.mapText = viz.addText3D('Press Left and Right to select.\nPress enter to start.')
		self.mapText.color(viz.BLACK)
		self.mapText.font('COURIER NEW')
		
		mat = viz.Matrix()
		mat.postTrans(-11,5,25)
		
		self.mapText.setMatrix(mat)
		self.mapText.visible( viz.OFF )
		
		self.maps = [self.shipment, self.factory]
		self.curMap = 0
		
		#Configuration for each map
		#[filename, startX, startY, startZ, [[enemy1x,enemy1y,enemy1z, enemy1radius][...]]]
		
		self.config = [['shipment.dae',50,2.5,50, [[50, 0, 88, 3.5], [39, 0, 71, 2], [72, 0, 110, 1.5], [102, 0, 96, 2], [69, 0, 80, 2], [110, 0, 33, 3]]],
					   ['factory.dae',15,2.0,5, [[15,0,9, 1]]]]
					
		self.callback(viz.KEYDOWN_EVENT, self.onKeyDown)
	
	# Advances past title, selects map, starts game
	def onKeyDown(self, key) :
		# If the user pushes enter on the title screen
		if key == viz.KEY_RETURN and not self.mapSelect :
			self.title.remove()
			self.shipment.visible(viz.ON)
			self.factory.visible(viz.ON)
			self.mapText.visible(viz.ON)
			self.mapSelect = True
		# If the user pushes enter on the map select screen
		elif key == viz.KEY_RETURN and self.mapSelect :
			# Start game at current map
			self.mapText.remove()
			g = Game(self.config[self.curMap])
			for map in self.maps :
				map.remove()
		# Move map selection left
		elif key == viz.KEY_LEFT and self.mapSelect :
			if self.curMap == 0 :
				self.curMap = len(self.maps)-1
			else :
				self.curMap -= 1
		# Move map selection right
		elif key == viz.KEY_RIGHT and self.mapSelect :
			if self.curMap == len(self.maps)-1 :
				self.curMap = 0
			else :
				self.curMap += 1
		
		# Set proper color for map selection
		for i in range(0,len(self.maps)) :
			if i == self.curMap :
				self.maps[self.curMap].color(viz.YELLOW)
			else :
				self.maps[i].color(viz.BLACK)

############
#GAME CLASS#
############
class Game(viz.EventClass) :
	def __init__(self, config) :
		viz.EventClass.__init__(self)
		viz.mouse(viz.ON)
		self.config = config
		
		# set first person movement controls and hide mouse
		viz.cam.setHandler(vizcam.WalkNavigate(moveScale=2.0,turnScale=2.0))
		viz.mouse.setVisible(viz.OFF)
		
		# initialize camera and map
		self.camera = viz.MainView
		self.map = viz.add( self.config[0] )
		self.camX = self.config[1]
		self.camY = self.config[2]
		self.camZ = self.config[3]
		self.camAngle = self.camera.getAxisAngle()
		self.camVector = [0,0,0]
		self.bulletVector = [0,0,0]
		
		# initialize gun
		self.gun = viz.add('gun.dae')
		
		# track active bullets
		self.bullets = []
		
		# reload indicator
		self.reload = viz.addText3D('   R\n   to Reload')
		self.reload.color(viz.WHITE)
		self.reload.font('COURIER NEW')
		self.reload.visible(viz.OFF)
		
		
		self.gunX = self.config[1]
		self.gunY = self.config[2]
		self.gunZ = self.config[3]+2
		mat = viz.Matrix()
		mat.postTrans(self.gunX,self.gunY,self.gunZ)
		self.gun.setMatrix(mat)
		
		# position the camera
		self.setCameraTransforms()
		
		# add enemies
		enemyCoords = self.config[4]
		self.enemyList = []
		counter = 0
		for x,y,z,radius in enemyCoords :
			self.enemyList.append(viz.add('model.dae'))
			mat = viz.Matrix()
			mat.postScale(0.125,0.125,0.125)
			mat.postTrans(x,y,z)
			self.enemyList[counter].setMatrix(mat)
			counter += 1	
	
		# scoring variables
		self.enemyCount = 0
		for enemy in self.enemyList :
			self.enemyCount += 1
		self.score = 0
		
		# game over variables
		self.gameIsOver = False
		self.gameOverText = None
		
		
		# add a sky
		self.sky = viz.add(viz.ENVIRONMENT_MAP, 'sky.jpg')
		self.skybox = viz.add( 'skydome.dlc' )
		self.skybox.texture( self.sky )
		
		# enable physics
		self.setPhysics()
		
		self.callback(viz.TIMER_EVENT, self.onTimer)
		self.callback(viz.MOUSEDOWN_EVENT, self.onMouseDown)
		self.callback(viz.COLLIDE_BEGIN_EVENT, self.onCollide)
		self.callback(viz.COLLISION_EVENT, self.camCollide)
		self.callback(viz.KEYDOWN_EVENT, self.onKeyDown)
		self.starttimer(0, 1/2, viz.FOREVER)
		
	# moves the camera and gun to the proper position
	def setCameraTransforms(self) :
		self.camAngle = self.camera.getAxisAngle()
		self.camera.setAxisAngle( self.camAngle )
		self.camera.setPosition( self.camX, self.camY, self.camZ )
		
		mat = viz.Matrix()
		mat.postAxisAngle(self.camAngle)
		self.camVector = mat.preMultVec(0,0,1)
		
		mat = viz.Matrix()
		mat.postAxisAngle(0,1,0, -105)
		mat.postAxisAngle(self.camAngle)
		mat.postTrans(self.camX+self.camVector[0], self.camY+self.camVector[1], self.camZ+self.camVector[2] )
		self.gun.setMatrix(mat)
		
		mat = viz.Matrix()
		mat.postScale(0.1, 0.1, 0.1)
		mat.postAxisAngle(self.camAngle)
		mat.postTrans(self.camX+self.camVector[0]*2, self.camY+self.camVector[1]*2, self.camZ+self.camVector[2]*2 )
		self.reload.setMatrix(mat)
	
	# enables physics for the map and camera
	def setPhysics(self) :
		viz.phys.enable()
		self.map.collideMesh()
		self.camera.collision( viz.ON )
		self.camera.stepSize( 0.5 )
		self.camera.gravity( 30 )
		self.camera.eyeheight(self.camY)
		#self.bullet.enable(viz.COLLIDE_NOTIFY)
		self.map.enable(viz.COLLIDE_NOTIFY)
		
		
		for i in range(0,len(self.enemyList)) :
			enemy = self.enemyList[i]
			enemy.enable(viz.COLLIDE_NOTIFY)
			Circle(enemy, self.config[4][i][3])
			enemy.collideBox()
	
	# keydown events
	def onKeyDown(self, key) :
		if key == 'r' and len(self.bullets) != 0 and not self.gameIsOver:
			viz.playSound('reload.wav')
			for bullet in self.bullets :
				bullet.remove()
			self.bullets = []
		
	# timer events
	def onTimer(self, num) :
		if len(self.bullets) >= 9 :
			self.reload.visible(viz.ON)
		else :
			self.reload.visible(viz.OFF)
			
		# camera timer
		if num == 0 :
			self.camX = self.camera.getPosition()[0]
			self.camY = self.camera.getPosition()[1]
			self.camZ = self.camera.getPosition()[2]
			self.camAngle = self.camera.getAxisAngle()
		
			self.setCameraTransforms()
			
	# collision events
	def onCollide(self, event) :
		for bullet in self.bullets :
			if (event.obj1 is bullet or event.obj2 is bullet) : # self.bullet.getVisible() :
				viz.playSound('quack.wav')
				for enemy in self.enemyList :
					if (event.obj1 is enemy or event.obj2 is enemy) :
						viz.playSound('quack.wav')
						enemy.remove()
						self.score += 1
						
				bullet.remove()
				
				if self.score == self.enemyCount :
					self.gameOver(True)
					
	# viewpoint collisions
	def camCollide(self, info) :
		for enemy in self.enemyList :
			if info.object is enemy :
				self.gameIsOver = True
				self.gameOver(False)
	
	# mousedown events
	def onMouseDown(self, button) :
		if button == viz.MOUSEBUTTON_LEFT and len(self.bullets) < 9:
			viz.playSound('gunshot.wav')
			bullet = viz.add('bullet.dae')
			self.bullets.append(bullet)
			
			bullet.collideBox(.25,.25,.25)
			mat = viz.Matrix()
			mat.postScale(0.05,0.05,0.05)
			mat.postAxisAngle(1,0,0, 90)
			mat.postAxisAngle(self.camAngle)
			self.bulletVector = self.camVector
			mat.postTrans(self.camX+self.bulletVector[0] + 0.025, self.camY+self.bulletVector[1] + 0.05, self.camZ+self.bulletVector[2] )
			bullet.setMatrix(mat)
			bullet.enable(viz.COLLIDE_NOTIFY)
			
			viz.phys.setGravity(0,0,0)
			bullet.setVelocity([self.bulletVector[0]*50,self.bulletVector[1]*50,self.bulletVector[2]*50])
			
	def gameOver(self, gameWon) :
			self.killtimer(0)
			self.killtimer(1)
			self.killtimer(2)
			
			self.map.remove()
			self.gun.remove()
			self.sky.remove()
			self.skybox.remove()
			viz.mouse(viz.OFF)
			
			for enemy in self.enemyList :
				enemy.remove()
				
			for bullet in self.bullets :
				bullet.remove()
			
			if not gameWon :
				text = viz.addText3D('Game Over \nScore: ' + str(self.score))
				text.color(viz.BLACK)
				text.font('COURIER NEW')
			else :
				text = viz.addText('You Win \nScore: ' + str(self.score))
				text.color(viz.BLACK)
				text.font('COURIER NEW')
				
			self.gameOverText = text
			
			mat = viz.Matrix()
			mat.postTrans(0,0,0)
			self.camera.setMatrix(mat)
			mat.postTrans(-4,2,15)
			self.gameOverText.setMatrix(mat)
			
			self.killtimer(0)
			self.killtimer(1)
			self.killtimer(2)
			
class Circle(viz.EventClass):
	def __init__(self,object,radius):
		#Initialize the base class
		viz.EventClass.__init__(self)
		
		#Store the object that we will be moving in a circle
		self.object = object

		#Initialize the offset
		self.offset = [object.getPosition()[0], object.getPosition()[1], object.getPosition()[2]]

		#Initialize the radius
		self.radius = radius

		#Initialize the speed (deg/sec)
		self.speed = 180

		#Initialize the starting angle
		self.angle = 0

		#Create a callback to our own event class function
		self.callback(viz.TIMER_EVENT,self.mytimer)

		#Start a perpetual timer for this event class
		self.starttimer(0,0.01,-1)

	def mytimer(self,num):
		
		#Increment the angle
		self.angle += self.speed * viz.elapsed()

		#Calculate the new position
		x = math.sin(viz.radians(self.angle)) * self.radius
		z = math.cos(viz.radians(self.angle)) * self.radius

		#Translate the object to the new position, accounting for the offset
		self.object.setAxisAngle(0,1,0, self.angle+90)
		self.object.setPosition([self.offset[0]+x,self.offset[1],self.offset[2]+z])

#############
#MAIN DRIVER#
#############
# set window size and name
#viz.window.setFullscreen(viz.ON)
viz.window.setSize(1366,768)
viz.window.setName("Shipment Navigation")

# set background color to white
viz.MainWindow.clearcolor(viz.WHITE)

# start the game
s = StartScreen()
viz.go()