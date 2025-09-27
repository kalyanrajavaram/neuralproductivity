import { useEffect, useState } from 'react';
import {
  Box, Heading, Text, Table, Thead, Tbody, Tr, Th, Td, Button,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalCloseButton,
  ModalBody, ModalFooter, VStack, HStack, Stat, StatLabel, StatNumber, StatHelpText, Divider
} from '@chakra-ui/react';

export default function StatsPage({ userId = 1 }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // For opening a saved session as a modal
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailSessionId, setDetailSessionId] = useState(null);
  const [detailAnalysis, setDetailAnalysis] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const res = await fetch(`http://localhost:8000/api/stats/${userId}`);
      const data = await res.json();
      setStats(data);
      setLoading(false);
    })();
  }, [userId]);

  const openSessionDetail = async (sessionId) => {
    const res = await fetch(`http://localhost:8000/api/sessions/${sessionId}`);
    const data = await res.json();
    // Normalize to your live analysis shape
    setDetailAnalysis({
      summary: data.summary,
      segments: data.segments,
      series_1hz: data.series_1hz,
      csv_paths: data.csv_paths,
    });
    setDetailSessionId(sessionId);
    setDetailOpen(true);
  };

  if (loading) return <Box p={6}><Text>Loading…</Text></Box>;
  if (!stats) return <Box p={6}><Text>No stats available.</Text></Box>;

  return (
    <Box p={6}>
      <Heading size="lg" mb={4}>Your Focus Stats</Heading>

      <Box mb={6}>
        <Heading size="md" mb={2}>Overview</Heading>
        <Text>Total Sessions: {stats.totals.total_sessions}</Text>
        <Text>Total Focus Time: {(stats.totals.total_focus_seconds/3600).toFixed(2)} hrs</Text>
        <Text>Average Focus Score: {Number(stats.totals.avg_focus_score).toFixed(3)}</Text>
      </Box>

      {/* You can plug daily_focus_trend into a chart library later */}
      <Box mb={6}>
        <Heading size="md" mb={2}>7-Day Trend</Heading>
        {stats.daily_focus_trend.length === 0 ? (
          <Text>No data yet.</Text>
        ) : (
          <ul>
            {stats.daily_focus_trend.map((d) => (
              <li key={d.date}>{d.date}: {Number(d.avg_focus).toFixed(3)}</li>
            ))}
          </ul>
        )}
      </Box>

      <Box mb={6}>
        <Heading size="md" mb={2}>By Category</Heading>
        {stats.category_breakdown.length === 0 ? (
          <Text>No categories yet.</Text>
        ) : (
          <ul>
            {stats.category_breakdown.map((c) => (
              <li key={c.category}>{c.category}: {c.count}</li>
            ))}
          </ul>
        )}
      </Box>

      <Box mb={6}>
        <Heading size="md" mb={2}>Recent Sessions</Heading>
        {stats.recent_sessions.length === 0 ? (
          <Text>No recent sessions.</Text>
        ) : (
          <Table size="sm" variant="simple">
            <Thead>
              <Tr>
                <Th>Date</Th>
                <Th>Task</Th>
                <Th>Category</Th>
                <Th isNumeric>Score</Th>
                <Th></Th>
              </Tr>
            </Thead>
            <Tbody>
              {stats.recent_sessions.map((s) => (
                <Tr key={s.id}>
                  <Td>{new Date(s.created_at).toLocaleString()}</Td>
                  <Td>{s.task || 'Untitled'}</Td>
                  <Td>{s.task_category || '—'}</Td>
                  <Td isNumeric>{(s.focus_score ?? 0).toFixed(3)}</Td>
                  <Td><Button size="sm" onClick={() => openSessionDetail(s.id)}>View</Button></Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Box>

      <Box>
        <a href={`http://localhost:8000/api/stats/${userId}/export.csv`}>
          <Button>Download CSV</Button>
        </a>
      </Box>

      {/* Detail Modal: shows saved analysis just like the live modal */}
      <Modal isOpen={detailOpen} onClose={() => setDetailOpen(false)} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Session #{detailSessionId}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {!detailAnalysis && <Text>No analysis available.</Text>}
            {detailAnalysis?.summary && (
              <VStack align="stretch" spacing={4}>
                <Stat>
                  <StatLabel>Mean Focus Score</StatLabel>
                  <StatNumber>{detailAnalysis.summary.mean_focus_score}</StatNumber>
                  <StatHelpText>EMA smoothed</StatHelpText>
                </Stat>
                <HStack>
                  <Stat><StatLabel>% Focused</StatLabel><StatNumber>{detailAnalysis.summary.pct_focused}%</StatNumber></Stat>
                  <Stat><StatLabel>% Partial</StatLabel><StatNumber>{detailAnalysis.summary.pct_partial}%</StatNumber></Stat>
                  <Stat><StatLabel>% Unfocused</StatLabel><StatNumber>{detailAnalysis.summary.pct_unfocused}%</StatNumber></Stat>
                </HStack>
                <Stat>
                  <StatLabel>Longest Focused Streak</StatLabel>
                  <StatNumber>{detailAnalysis.summary.longest_focused_streak_s}s</StatNumber>
                </Stat>
                <Divider />
                {Array.isArray(detailAnalysis.segments) && detailAnalysis.segments.length > 0 && (
                  <>
                    <Heading size="md">Focused Segments</Heading>
                    <VStack align="stretch" spacing={2} maxH="240px" overflowY="auto">
                      {detailAnalysis.segments.map((seg, i) => (
                        <Box key={i} p={3} borderWidth="1px" borderRadius="md">
                          <Text><b>Start:</b> {seg.start_s.toFixed?.(2) ?? seg.start_s}s</Text>
                          <Text><b>End:</b> {seg.end_s.toFixed?.(2) ?? seg.end_s}s</Text>
                          <Text><b>Duration:</b> {seg.duration_s.toFixed?.(2) ?? seg.duration_s}s</Text>
                        </Box>
                      ))}
                    </VStack>
                  </>
                )}
              </VStack>
            )}
          </ModalBody>
          <ModalFooter><Button onClick={() => setDetailOpen(false)}>Close</Button></ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
