import { Box, Heading, Text, VStack, Stat, StatLabel, StatNumber, SimpleGrid } from '@chakra-ui/react';

function Dashboard() {
  // Hardcoded sample stats (you'll replace with real data later)
  const totalSessions = 12;
  const totalFocusTimeMinutes = 300; // e.g., 5 hours total
  const averageSessionLength = 25; // in minutes
  const bestFocusSession = 40; // in minutes

  return (
    <Box
      minH="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      bg="gray.50"
      px={4}
    >
      <VStack spacing={8}>
        <Heading size="xl" color="teal.700">
          Productivity Dashboard
        </Heading>

        <Text fontSize="lg" color="gray.600">
          Here's a summary of your sessions so far:
        </Text>

        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} maxW="600px">
          <Stat>
            <StatLabel>Total Sessions Completed</StatLabel>
            <StatNumber>{totalSessions}</StatNumber>
          </Stat>

          <Stat>
            <StatLabel>Total Focus Time</StatLabel>
            <StatNumber>{totalFocusTimeMinutes} min</StatNumber>
          </Stat>

          <Stat>
            <StatLabel>Average Session Length</StatLabel>
            <StatNumber>{averageSessionLength} min</StatNumber>
          </Stat>

          <Stat>
            <StatLabel>Longest Focus Session</StatLabel>
            <StatNumber>{bestFocusSession} min</StatNumber>
          </Stat>
        </SimpleGrid>
      </VStack>
    </Box>
  );
}

export default Dashboard;
