exports.handler = async (event) => {
  console.log("Communicating status", event);
  return { status: "communicated", incidentId: event.incidentId };
};