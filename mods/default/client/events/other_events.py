import pygame
from copy import deepcopy

import util
from api.packets import SendCommandPacket, LoginPacket
from api.entity import Player

def onGameMouseClick(game, mousePos, event):
    '''
    Event Hook: onMouseClick
    Handle a mouse click on vehicles, players and entities
    '''
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').gameGui:

        screen = game.getGui()[1].screen

        w = screen.get_width()
        h = screen.get_height()

        # Get the main player's position, to calculate the screen positions of the other players
        mainAbsPos = game.player.getAbsPos()

        # Check for mousepress on vehicles first
        for vehicle in game.world.vehicles:
            # Get the difference in position
            deltaPos = [vehicle.pos[a]-mainAbsPos[a] for a in range(2)]
            # Get the player image size
            size = vehicle.getImage(game.modLoader.gameRegistry.resources).get_rect()
            # Adjust position accordingly
            pos = [w//2+deltaPos[0]*40-size.width//2, h//2+deltaPos[1]*40-size.height//2]

            # Create a rect based on the vehicle image
            rect = pygame.Rect(pos+[size.width, size.height])
            if rect.collidepoint(mousePos):
                # User has clicked on the vehicle
                vehicle.mountRider(game.player)
                return

        # Then check for mousepress on players
        for player in game.world.players:
            # Get the difference in position
            deltaPos = [player.pos[a]-mainAbsPos[a] for a in range(2)]
            # Get the player image size
            size = player.smallImg.get_rect()
            # Adjust position accordingly
            pos = [w//2+deltaPos[0]*40-size.width//2, h//2+deltaPos[1]*40-size.height//2]

            # Create a rect based on the player image
            rect = pygame.Rect(pos+[size.width, size.height])
            if rect.collidepoint(mousePos):
                # User has clicked on the player
                chatOverlay = game.getModInstance('ClientMod').chatOverlay
                if not game.getGUIState().isOverlayOpen(chatOverlay):
                    game.openOverlay(chatOverlay, game, player.username)
                return

def onGameKeyPress(game, event):
    '''
    Event Hook: onKeyPress
    Handle the opening and closing of the messaging overlay
    '''
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').gameGui:
        chatOverlay = game.getModInstance('ClientMod').chatOverlay

        if not game.getGUIState().isOverlayOpen(chatOverlay):
            if event.key == pygame.K_t:
                game.openOverlay(chatOverlay, game)
            elif event.key == pygame.K_u:
                game.openOverlay(chatOverlay, game, 'local')
            elif event.key == pygame.K_e:
                game.openGui(game.getModInstance('ClientMod').inventoryGui, game)

        elif event.key == pygame.K_ESCAPE:
            game.getGUIState().closeOverlay(chatOverlay)

        if event.key == pygame.K_m:
            game.getModInstance('ClientMod').packetPipeline.sendToServer(SendCommandPacket('/message global random test message'))

        if event.key == pygame.K_b:
            game.getModInstance('ClientMod').packetPipeline.sendToServer(SendCommandPacket('/spawn Bear'))

def onInvKeyPress(game, event):
    '''
    Event Hook: onKeyPress
    Handle the key press events while in the inventory screen
    '''
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').inventoryGui:
        if event.key == pygame.K_ESCAPE:
            game.restoreGui()

def onCommand(game, commandClass, username, args):
    '''
    Event Hook: onCommand
    Extend the default behaviour for some commands
    '''
    if commandClass.__name__ == 'MessageCommand':
        message = ' '.join(args[1:])
        modInstance = game.getModInstance('ClientMod')
        modInstance.chatMessages[args[0]] = modInstance.chatMessages.get(args[0], []) + [message]
        print(' '.join(args[1:]))

def onPacketReceived(game, packet):
    '''
    Event Hook: onPacketReceived
    Hook additional behaviour into the vanilla API packets
    '''
    if packet.__class__.__name__ == 'DisconnectPacket':
        # Open a GUI that displays the message, and disconnect them
        game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, packet.message)

    elif packet.__class__.__name__ == 'ResetPlayerPacket':
        # Tell the game that the player is synced
        game.player.synced = True

    elif packet.__class__.__name__ == 'InvalidLoginPacket':
        # Tell the player that their username is already taken
        game.openGui(game.getModInstance('ClientMod').mainMenuGui)
        game.getGui()[1].error = 'That Username Is Already Taken.'

    elif packet.__class__.__name__ == 'WorldUpdatePacket':
        # Fetch images of new players
        for p, player in enumerate(game.world.players):
            if player.img == None:
                game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchPlayerImagePacket(player), util.NON_PRIMARY)

def onDisconnect(game, message):
    '''
    Event Hook: onDisconnect
    Handle the opening of the disconnected screen when the client disconnects
    '''
    # Show the message
    game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, message)
    # Flush the connection buffers
    for conn in game.getModInstance('ClientMod').packetPipeline.connections.keys():
        game.getModInstance('ClientMod').packetPipeline.connections[conn].connObj.recv(65536)

def onClientConnected(game):
    '''
    Event Hook: onClientConnected
    Apply the extra property to the client player when the connection to the server is established
    '''
    # Send a login packet
    game.getModInstance('ClientMod').packetPipeline.sendToServer(LoginPacket(game.player))
    print('connection to server established')
    game.player.setProperty('relPos2', game.getModInstance('ClientMod').relPos2Property)

def onPlayerLogin(game, player):
    '''
    Event Hook: onPlayerLogin
    Open the player customisation screen when the client logs into the server
    '''
    # Show the player customisation screen
    # TODO Change this later
    game.openGui(game.getModInstance('ClientMod').gameGui, game)
    # game.openGui(game.getModInstance('ClientMod').playerDrawGui, game)

def onPlayerUpdate(game, player, oldPlayers):
    '''
    Event Hook: onPlayerUpdate
    Apply the updates to other player attributes from the server
    '''
    # If the player being updated is the client player, skip it
    if player.username == game.player.username:
        return
    for p in range(len(oldPlayers)):
        if oldPlayers[p].username == player.username:
            # Update vanilla player properties
            oldPlayers[p].health = player.health

            # Update the modded properties
            props = oldPlayers[p].getProperty('worldUpdate')
            props.props['newPos'] = player.pos
            props.props['updateTick'] = game.tick
            oldPlayers[p].setProperty('worldUpdate', props)

            return

    player.setProperty('worldUpdate', game.getModInstance('ClientMod').worldUpdateProperty)
    oldPlayers.append(player)

def onEntitySync(game, entity, entities):
    '''
    Event Hook: onEntitySync
    Apply the updates to the entity from the server
    '''
    # If the player being updated is the client player, skip it
    for e in range(len(entities)):
        if entities[e].uuid == entity.uuid:
            # Update vanilla player properties
            entities[e].health = entity.health

            # Update the modded properties
            props = entities[e].getProperty('worldUpdate')
            props.props['newPos'] = entity.pos
            props.props['updateTick'] = game.tick
            entities[e].setProperty('worldUpdate', props)

            return

    entity.setProperty('worldUpdate', deepcopy(game.getModInstance('ClientMod').worldUpdateProperty))
    entities.append(entity)

def onDimensionChange(game, entity, oldDimension, newDimension):
    '''
    Event Hook: onDimensionChange
    Run logic when an entity changes dimension
    '''
    if isinstance(entity, Player) and entity.username == game.player.username:
        # Check if it's the client player switching dimension
        message = 'Entering '+game.getDimension(newDimension).getName()
        game.openGui(game.getModInstance('ClientMod').enteringGui, message)
