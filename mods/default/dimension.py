from api.dimension import *

class DefaultChunkProvider(ChunkProvider):
    def getName(self):
        return 'the Overworld'

    def generate(self, pos, gameRegistry):
        start = time.time()
        xPos, yPos = pos
        xPos = round(xPos)
        yPos = round(yPos)

        # Generate Simplex Noise for the world
        noiseMap = [[noise.snoise2(x, y, 8, 1.4, 0.45, base=gameRegistry.seed)/2+0.5 for x in range(xPos-150, xPos+151)] for y in range(yPos-105, yPos+106)]
        biomeSize = self.biomeSize
        biomeNoise = [[noise.snoise2(x, y, 7, 3, 0.6-(biomeSize*0.1), base=gameRegistry.seed/2)/2+0.5 for x in range(xPos-150, xPos+151)] for y in range(yPos-105, yPos+106)]
        detailNoise = []

        biomes = self.biomes

        # Generate an empty starting biome map
        width, height = (120, 84)
        biomeMap = TileMap(width, height)

        # Scatter some biomes in
        for y, row in enumerate(biomeMap.map):
            for x, tile in enumerate(row):
                biomeMap.map[y][x] = biomes[round(biomeNoise[y][x]*(len(biomes)-1))]()
                biomeMap.map[y][x].setTileType(noiseMap[y][x], 0, gameRegistry.resources)

        # Choose tile types and generate entities, houses, trees, etc in the biomes
        # biomeMap.finalPass(noiseMap, detailNoise, gameRegistry.resources)

        print('Time taken: '+str(time.time()-start)+' seconds')

        return biomeMap
