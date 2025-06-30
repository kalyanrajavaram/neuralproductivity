   import { Box, Heading, Button, VStack, Text } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const navigate = useNavigate();

  return (
    <Box
      minH="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      bg="gray.100"
      px={4}
    >
      <VStack spacing={8}>
        <Heading size="2xl" color="teal.700">
          Welcome to Smart Pomodoro App
        </Heading>

        <Text fontSize="lg" color="gray.600">
          Choose where you want to go:
        </Text>

        <VStack spacing={4}>
          <Button colorScheme="teal" size="lg" onClick={() => navigate('/timer')}>
            Start Pomodoro Timer
          </Button>

          <Button colorScheme="blue" size="lg" onClick={() => navigate('/preferences')}>
            Set Preferences
          </Button>

          <Button colorScheme="purple" size="lg" onClick={() => navigate('/dashboard')}>
            View Dashboard
          </Button>
        </VStack>
      </VStack>
    </Box>
  );
}

export default Dashboard;