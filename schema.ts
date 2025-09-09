import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, integer } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const services = pgTable("services", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  description: text("description").notNull(),
  basePrice: integer("base_price").notNull(),
  category: text("category").notNull(),
  duration: integer("duration").notNull(), // in minutes
  isActive: varchar("is_active").notNull().default("true"),
});

export const serviceProviders = pgTable("service_providers", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  email: text("email").notNull(),
  phone: text("phone").notNull(),
  rating: integer("rating").notNull().default(5),
  reviewCount: integer("review_count").notNull().default(0),
  experience: text("experience").notNull(),
  specialties: text("specialties").array(),
  isActive: varchar("is_active").notNull().default("true"),
});

export const appointments = pgTable("appointments", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  serviceId: varchar("service_id").notNull(),
  providerId: varchar("provider_id").notNull(),
  customerName: text("customer_name").notNull(),
  customerEmail: text("customer_email").notNull(),
  customerPhone: text("customer_phone").notNull(),
  propertyAddress: text("property_address").notNull(),
  appointmentDate: timestamp("appointment_date").notNull(),
  appointmentTime: text("appointment_time").notNull(),
  specialInstructions: text("special_instructions"),
  status: text("status").notNull().default("confirmed"),
  totalPrice: integer("total_price").notNull(),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

export const timeSlots = pgTable("time_slots", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  providerId: varchar("provider_id").notNull(),
  date: text("date").notNull(), // YYYY-MM-DD format
  time: text("time").notNull(), // HH:MM format
  isAvailable: varchar("is_available").notNull().default("true"),
});

export const insertServiceSchema = createInsertSchema(services).omit({
  id: true,
});

export const insertServiceProviderSchema = createInsertSchema(serviceProviders).omit({
  id: true,
});

export const insertAppointmentSchema = createInsertSchema(appointments).omit({
  id: true,
  createdAt: true,
}).extend({
  appointmentDate: z.string(), // Accept string and convert to Date
});

export const insertTimeSlotSchema = createInsertSchema(timeSlots).omit({
  id: true,
});

export type Service = typeof services.$inferSelect;
export type ServiceProvider = typeof serviceProviders.$inferSelect;
export type Appointment = typeof appointments.$inferSelect;
export type TimeSlot = typeof timeSlots.$inferSelect;
export type InsertService = z.infer<typeof insertServiceSchema>;
export type InsertServiceProvider = z.infer<typeof insertServiceProviderSchema>;
export type InsertAppointment = z.infer<typeof insertAppointmentSchema>;
export type InsertTimeSlot = z.infer<typeof insertTimeSlotSchema>;
