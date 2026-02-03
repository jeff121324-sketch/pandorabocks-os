class PersonaGate:
    """
    強制人格在 risk snapshot 當下回應
    """

    def __init__(self, personas):
        self.personas = personas

    def on_risk_snapshot(self, event):
        responses = []

        for persona in self.personas:
            r = persona.on_risk_snapshot(event)
            responses.append(r)

        # 🔥 將人格回應送入治理 / 決策
        event.bus.publish(
            PBEvent(
                type="persona.responses",
                payload={
                    "responses": responses,
                    "risk": event.payload,
                },
                source="persona_gate",
            )
        )