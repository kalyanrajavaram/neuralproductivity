import { Box, Container } from '@chakra-ui/react';
import PomodoroTimer from '../components/PomodoroTimer';

export default function Home() {
  return (
    <Container maxW="container.md" centerContent py={10}>
      <Box width="100%">
        <PomodoroTimer />
      </Box>
    </Container>
  );
}
