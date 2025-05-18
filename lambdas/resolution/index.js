exports.handler = async (event) => {
  console.log("Resolving incident", event);
  return { status: "resolved", incidentId: event.incidentId };
};