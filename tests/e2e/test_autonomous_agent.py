#!/usr/bin/env python3
"""
Unit tests for Phase 3 autonomous roasting agent.
Tests are fast - no real MCP connections or OpenAI API calls.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Mock the imports before importing the agent
import sys
sys.path.insert(0, '/Users/sertanyamaner/git/coffee-roasting')

# We'll test the agent logic without actual MCP/OpenAI connections


class TestRoastingAgentLogic:
    """Test RoastingAgent business logic without external dependencies."""
    
    def setup_method(self):
        """Setup test fixtures."""
        from Phase3.autonomous_agent import RoastingAgent
        
        # Mock dependencies
        self.mock_ai_client = Mock()
        self.mock_roaster_session = AsyncMock()
        self.mock_detection_session = AsyncMock()
        
        # Create agent with mocks
        self.agent = RoastingAgent(
            self.mock_ai_client,
            self.mock_roaster_session,
            self.mock_detection_session
        )
    
    def test_agent_initialization(self):
        """Test agent initializes with correct state."""
        assert self.agent.roast_start_time is None
        assert self.agent.first_crack_time is None
        assert self.agent.first_crack_detected is False
        assert self.agent.roast_log == []
    
    def test_log_event(self):
        """Test event logging."""
        self.agent.log_event("test_event", {"key": "value"})
        
        assert len(self.agent.roast_log) == 1
        log_entry = self.agent.roast_log[0]
        assert log_entry["event"] == "test_event"
        assert log_entry["data"] == {"key": "value"}
        assert "timestamp" in log_entry
    
    @pytest.mark.asyncio
    async def test_create_roast_plan(self):
        """Test roast plan creation with mocked GPT."""
        # Mock GPT response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "bean_type": "Ethiopian Yirgacheffe",
            "target_roast": "light",
            "initial_heat": 80,
            "initial_fan": 30,
            "target_fc_temp": 196,
            "target_fc_time": 11,
            "post_fc_adjustments": "reduce heat",
            "target_total_time": 13,
            "drop_criteria": "2 min after FC"
        })
        self.mock_ai_client.chat.completions.create.return_value = mock_response
        
        plan = await self.agent.create_roast_plan("Test roast prompt")
        
        assert plan["bean_type"] == "Ethiopian Yirgacheffe"
        assert plan["initial_heat"] == 80
        assert plan["initial_fan"] == 30
        assert self.mock_ai_client.chat.completions.create.called
    
    @pytest.mark.asyncio
    async def test_start_roast(self):
        """Test roast start sequence."""
        plan = {
            "initial_heat": 80,
            "initial_fan": 30,
            "bean_type": "Test"
        }
        
        # Mock tool calls
        self.mock_roaster_session.call_tool.return_value = Mock()
        self.mock_detection_session.call_tool.return_value = Mock()
        
        await self.agent.start_roast(plan)
        
        # Verify tools were called
        assert self.mock_roaster_session.call_tool.call_count == 3  # start, heat, fan
        assert self.mock_detection_session.call_tool.call_count == 1  # start detection
        
        # Verify roast started
        assert self.agent.roast_start_time is not None
        assert len(self.agent.roast_log) == 1
    
    @pytest.mark.asyncio
    async def test_handle_first_crack(self):
        """Test first crack detection handling."""
        self.agent.roast_start_time = datetime.now()
        
        status = {"bean_temp_c": 175.5, "heat_level": 80}
        plan = {"bean_type": "Test"}
        
        # Mock report_first_crack
        self.mock_roaster_session.call_tool.return_value = Mock()
        
        await self.agent.handle_first_crack(status, plan)
        
        assert self.agent.first_crack_detected is True
        assert self.agent.first_crack_time is not None
        assert self.mock_roaster_session.call_tool.called
    
    @pytest.mark.asyncio
    async def test_finish_roast(self):
        """Test roast completion sequence."""
        self.agent.roast_start_time = datetime.now()
        
        # Mock tool calls
        self.mock_detection_session.call_tool.return_value = Mock()
        self.mock_roaster_session.call_tool.return_value = Mock()
        
        await self.agent.finish_roast()
        
        # Verify sequence: stop detection, drop beans, start cooling
        assert self.mock_detection_session.call_tool.call_count == 1
        assert self.mock_roaster_session.call_tool.call_count == 2


class TestDecisionLogic:
    """Test AI decision-making logic."""
    
    @pytest.mark.asyncio
    async def test_make_decision_continue(self):
        """Test decision to continue roasting."""
        from Phase3.autonomous_agent import RoastingAgent
        
        mock_ai = Mock()
        mock_roaster = AsyncMock()
        mock_detection = AsyncMock()
        
        agent = RoastingAgent(mock_ai, mock_roaster, mock_detection)
        agent.roast_start_time = datetime.now()
        agent.first_crack_time = datetime.now()
        
        # Mock GPT decision: continue
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "continue",
            "reason": "Temperature rising steadily",
            "heat_adjustment": None,
            "fan_adjustment": None
        })
        mock_ai.chat.completions.create.return_value = mock_response
        
        status = {"bean_temp_c": 185, "heat_level": 70, "fan_speed": 50}
        plan = {"bean_type": "Test", "target_roast": "light", "target_total_time": 13}
        
        should_continue = await agent.make_decision(status, plan, 10.5)
        
        assert should_continue is True
        assert mock_roaster.call_tool.call_count == 0  # No adjustments
    
    @pytest.mark.asyncio
    async def test_make_decision_adjust(self):
        """Test decision to adjust parameters."""
        from Phase3.autonomous_agent import RoastingAgent
        
        mock_ai = Mock()
        mock_roaster = AsyncMock()
        mock_detection = AsyncMock()
        
        agent = RoastingAgent(mock_ai, mock_roaster, mock_detection)
        agent.roast_start_time = datetime.now()
        agent.first_crack_time = datetime.now()
        
        # Mock GPT decision: adjust
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "adjust",
            "reason": "Reduce heat for development",
            "heat_adjustment": 60,
            "fan_adjustment": 60
        })
        mock_ai.chat.completions.create.return_value = mock_response
        
        status = {"bean_temp_c": 188, "heat_level": 80, "fan_speed": 40}
        plan = {"bean_type": "Test", "target_roast": "light", "target_total_time": 13}
        
        should_continue = await agent.make_decision(status, plan, 11.0)
        
        assert should_continue is True
        assert mock_roaster.call_tool.call_count == 2  # Heat and fan adjustments


class TestAuth0Token:
    """Test Auth0 token acquisition."""
    
    @patch('Phase3.autonomous_agent.requests.post')
    def test_get_auth0_token_success(self, mock_post):
        """Test successful token acquisition."""
        from Phase3.autonomous_agent import get_auth0_token
        
        # Mock response
        mock_post.return_value.json.return_value = {
            "access_token": "test_token_123",
            "token_type": "Bearer",
            "expires_in": 86400
        }
        mock_post.return_value.raise_for_status = Mock()
        
        token = get_auth0_token()
        
        assert token == "test_token_123"
        assert mock_post.called
    
    @patch('Phase3.autonomous_agent.requests.post')
    def test_get_auth0_token_failure(self, mock_post):
        """Test token acquisition failure handling."""
        from Phase3.autonomous_agent import get_auth0_token
        import requests
        
        # Mock failure
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("401")
        
        with pytest.raises(requests.HTTPError):
            get_auth0_token()


class TestRoastPromptParsing:
    """Test roast prompt parsing and plan generation."""
    
    @pytest.mark.asyncio
    async def test_plan_generation_with_defaults(self):
        """Test plan generation fills in reasonable defaults."""
        from Phase3.autonomous_agent import RoastingAgent
        
        mock_ai = Mock()
        mock_roaster = AsyncMock()
        mock_detection = AsyncMock()
        
        agent = RoastingAgent(mock_ai, mock_roaster, mock_detection)
        
        # Mock minimal GPT response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "bean_type": "Unknown",
            "target_roast": "medium",
            "initial_heat": 80,
            "initial_fan": 30,
            "target_fc_temp": 170,
            "target_fc_time": 8,
            "post_fc_adjustments": "standard",
            "target_total_time": 11,
            "drop_criteria": "2 min after FC"
        })
        mock_ai.chat.completions.create.return_value = mock_response
        
        plan = await agent.create_roast_plan("Roast some beans")
        
        assert "bean_type" in plan
        assert "initial_heat" in plan
        assert "initial_fan" in plan
        assert 0 <= plan["initial_heat"] <= 100
        assert 0 <= plan["initial_fan"] <= 100


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
