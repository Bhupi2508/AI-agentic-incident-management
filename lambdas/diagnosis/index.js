exports.handler = async (event) => {
  console.log("Diagnosing incident", event);
  return { status: "diagnosed", incidentId: event.incidentId };
};