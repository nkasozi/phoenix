import ClassifierService from "./classifierService";
import GatherService from "./gatherService";
import JobRunService from "./jobRunService";
import StorageService from "./storageService";
import UserService from "./userService";

export const storageService = new StorageService();
export const jobRunService = new JobRunService();
export const gatherService = new GatherService();
export const classifierService = new ClassifierService();
export const userService = new UserService();
