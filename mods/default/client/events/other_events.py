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
        game.openGUI[1].error = 'That Username Is Already Taken.'

    elif packet.__class__.__name__ == 'WorldUpdatePacket':
        # Fetch images of new players
        for p, player in enumerate(game.world.players):
            if player.img == None:
                game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchPlayerImagePacket(player))

def onDisconnect(game):
    '''
    Event Hook: onDisconnect
    Handle the opening of the disconnected screen when the client disconnects
    '''
    game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, 'Server Connection Reset')

def onClientConnected(game):
    '''
    Event Hook: onClientConnected
    Apply the extra property to the client player when the connection to the server is established
    '''
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
