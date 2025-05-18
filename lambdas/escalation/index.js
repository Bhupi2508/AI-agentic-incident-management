exports.handler = async (event) => {
  console.log("Escalating incident", event);
  return { status: "escalated", incidentId: event.incidentId };
};